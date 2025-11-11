import argparse
import concurrent.futures
import contextlib
import hashlib
import json
import os
import re
import threading
import time
from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse, urlunparse

import requests

class SimpleDirIndexParser(HTMLParser):
    def __init__(self, base_url):
        super().__init__()
        self.links = []
        self.base_url = base_url
    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return
        href = None
        for k, v in attrs:
            if k.lower() == "href":
                href = v
                break
        if href is None:
            return
        if href in ("../", ".."):
            return
        absolute = urljoin(self.base_url, href)
        self.links.append(absolute)

def normalize_url(u):
    p = urlparse(u)
    path = re.sub(r"/+", "/", p.path)
    if p.query or p.fragment:
        return urlunparse((p.scheme, p.netloc, path, "", "", ""))
    return urlunparse((p.scheme, p.netloc, path, p.params, p.query, p.fragment))

def ensure_dir(p):
    os.makedirs(p, exist_ok=True)

class Manifest:
    def __init__(self, path):
        self.path = path
        self._lock = threading.Lock()
        self.data = {}
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                try:
                    self.data = json.load(f)
                except Exception:
                    self.data = {}
    def get(self, key):
        with self._lock:
            return self.data.get(key)
    def set(self, key, value):
        with self._lock:
            self.data[key] = value
    def save(self):
        tmp = self.path + ".tmp"
        with self._lock:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, sort_keys=True)
            os.replace(tmp, self.path)

class Downloader:
    def __init__(self, base_url, dest, accept_exts, workers, timeout, retries, delay, manifest_path, dry_run, user_agent):
        self.base_url = normalize_url(base_url.rstrip("/") + "/")
        self.dest = os.path.abspath(dest)
        ensure_dir(self.dest)
        self.accept_exts = set()
        if accept_exts:
            for e in accept_exts.split(","):
                e = e.strip()
                if not e:
                    continue
                if not e.startswith("."):
                    e = "." + e
                self.accept_exts.add(e.lower())
        self.workers = workers
        self.timeout = timeout
        self.retries = retries
        self.delay = delay
        self.manifest = Manifest(manifest_path if manifest_path else os.path.join(self.dest, ".argo_manifest.json"))
        self.dry_run = dry_run
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        self._dir_lock = threading.Lock()
        self._found_files = []
        self._found_dirs = []
    def _within_base(self, url):
        u = normalize_url(url)
        return u.startswith(self.base_url)
    def _relpath_from_url(self, url):
        u = normalize_url(url)
        base = self.base_url
        if not u.startswith(base):
            return None
        rel = u[len(base):]
        return rel
    def _local_path(self, url):
        rel = self._relpath_from_url(url)
        if rel is None:
            return None
        return os.path.join(self.dest, rel.replace("/", os.sep))
    def _accepted(self, url):
        if not self.accept_exts:
            return True
        path = urlparse(url).path
        _, ext = os.path.splitext(path)
        return ext.lower() in self.accept_exts
    def _request(self, method, url, **kwargs):
        last_exc = None
        for i in range(self.retries + 1):
            try:
                r = self.session.request(method, url, timeout=self.timeout, **kwargs)
                if r.status_code >= 500:
                    raise requests.RequestException(f"Server error {r.status_code}")
                return r
            except Exception as e:
                last_exc = e
                if i < self.retries:
                    time.sleep(self.delay * (2 ** i))
        if last_exc:
            raise last_exc
    def _parse_dir(self, url):
        try:
            r = self._request("GET", url)
        except Exception:
            return []
        ctype = r.headers.get("Content-Type", "")
        if "text/html" not in ctype:
            return []
        parser = SimpleDirIndexParser(url)
        with contextlib.suppress(Exception):
            parser.feed(r.text)
        links = []
        for link in parser.links:
            if not self._within_base(link):
                continue
            links.append(normalize_url(link))
        return links
    def _is_dir_link(self, url):
        return normalize_url(url).endswith("/")
    def crawl(self):
        stack = [self.base_url]
        seen = set()
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            entries = self._parse_dir(cur)
            for e in entries:
                if self._is_dir_link(e):
                    rel = self._relpath_from_url(e)
                    if rel is not None:
                        with self._dir_lock:
                            self._found_dirs.append(e)
                    stack.append(e)
                else:
                    if self._accepted(e):
                        with self._dir_lock:
                            self._found_files.append(e)
        return list(self._found_files)
    def _should_download(self, url, head):
        rel = self._relpath_from_url(url)
        if rel is None:
            return False
        meta = self.manifest.get(url)
        lm = head.headers.get("Last-Modified")
        etag = head.headers.get("ETag")
        size = head.headers.get("Content-Length")
        changed = False
        if meta is None:
            changed = True
        else:
            if etag and meta.get("etag") != etag:
                changed = True
            elif lm and meta.get("last_modified") != lm:
                changed = True
            elif size and str(meta.get("size")) != str(size):
                changed = True
        local = self._local_path(url)
        if not os.path.isfile(local):
            changed = True
        return changed
    def _update_manifest(self, url, r):
        etag = r.headers.get("ETag")
        lm = r.headers.get("Last-Modified")
        size = r.headers.get("Content-Length")
        self.manifest.set(url, {"etag": etag, "last_modified": lm, "size": size, "ts": int(time.time())})
    def _download_one(self, url):
        head = self._request("HEAD", url, allow_redirects=True)
        if head.status_code == 405 or head.status_code >= 400:
            head = self._request("GET", url, stream=True)
            head.close()
        if not self._should_download(url, head):
            return (url, "skipped")
        local_path = self._local_path(url)
        if local_path is None:
            return (url, "skipped")
        ensure_dir(os.path.dirname(local_path))
        if self.dry_run:
            return (url, "would-download")
        tmp_path = local_path + ".part"
        start = 0
        accept_ranges = False
        with contextlib.suppress(Exception):
            if os.path.exists(tmp_path):
                start = os.path.getsize(tmp_path)
            else:
                if os.path.exists(local_path):
                    start = os.path.getsize(local_path)
                    tmp_path = local_path + ".part"
        ar = head.headers.get("Accept-Ranges", "").lower()
        if "bytes" in ar:
            accept_ranges = True
        headers = {}
        if accept_ranges and start > 0:
            headers["Range"] = f"bytes={start}-"
        r = self._request("GET", url, stream=True, headers=headers)
        mode = "ab" if headers.get("Range") else "wb"
        with open(tmp_path, mode) as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if not chunk:
                    continue
                f.write(chunk)
        os.replace(tmp_path, local_path)
        self._update_manifest(url, r)
        return (url, "downloaded")
    def download_all(self, files):
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as ex:
            futs = [ex.submit(self._download_one, u) for u in files]
            for fut in concurrent.futures.as_completed(futs):
                with contextlib.suppress(Exception):
                    results.append(fut.result())
        self.manifest.save()
        return results

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="https://data-argo.ifremer.fr/geo/indian_ocean/2025/", help="Base directory URL to mirror")
    ap.add_argument("--dest", required=True, help="Destination directory")
    ap.add_argument("--accept", default="", help="Comma-separated list of file extensions to include, e.g. .nc,.csv")
    ap.add_argument("--workers", type=int, default=8, help="Concurrent downloads")
    ap.add_argument("--timeout", type=int, default=60, help="Per-request timeout seconds")
    ap.add_argument("--retries", type=int, default=3, help="Retry count")
    ap.add_argument("--delay", type=float, default=1.0, help="Initial retry delay seconds")
    ap.add_argument("--manifest", default="", help="Path to manifest JSON; defaults under dest")
    ap.add_argument("--dry-run", action="store_true", help="List actions without downloading")
    ap.add_argument("--user-agent", default="argo-mirror/1.0", help="HTTP User-Agent")
    args = ap.parse_args()
    dl = Downloader(
        base_url=args.base_url,
        dest=args.dest,
        accept_exts=args.accept,
        workers=args.workers,
        timeout=args.timeout,
        retries=args.retries,
        delay=args.delay,
        manifest_path=args.manifest,
        dry_run=args.dry_run,
        user_agent=args.user_agent,
    )
    files = dl.crawl()
    results = dl.download_all(files)
    skipped = sum(1 for _, s in results if s == "skipped")
    dled = sum(1 for _, s in results if s == "downloaded")
    would = sum(1 for _, s in results if s == "would-download")
    print(f"found={len(files)} downloaded={dled} skipped={skipped} would_download={would}")

if __name__ == "__main__":
    main()
