#!/usr/bin/env python3
"""
Downloads BGC-Argo NetCDF files from IFREMER based on bio-profile index.
No database operations - just downloads files.
"""

import os
import sys
import json
import time
import logging
import argparse
from datetime import datetime
from typing import List, Dict, Any
import requests


LOG = logging.getLogger("bgc_download")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class BGCArgoDownloader:
    """Downloads BGC-Argo files based on bio-profile index."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.download_dir = config["download_dir"]
        
        os.makedirs(self.download_dir, exist_ok=True)
        os.makedirs(config["log_dir"], exist_ok=True)

        # Setup logging
        fh = logging.FileHandler(os.path.join(config["log_dir"], 
                                              f"bgc_download_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"))
        fh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        LOG.addHandler(fh)

        self.stats = {
            "found": 0,
            "downloaded": 0,
            "skipped_404": 0,
            "skipped_existing": 0,
            "errors": []
        }
        self.failed_urls = set()  # Track 404s to avoid retrying

    def discover_bgc_files(self) -> List[Dict[str, Any]]:
        """Discover BGC files from the bio-profile index."""
        LOG.info("Downloading BGC bio-profile index...")
        url = self.config["index_url"]
        target_params = set(self.config["target_params"])
        org_prefix = self.config.get("organization_prefix", "incois/")
        
        try:
            response = requests.get(url, timeout=120)
            response.raise_for_status()
        except Exception as e:
            LOG.error(f"Failed to download index: {e}")
            return []

        lines = response.text.splitlines()
        
        # Find header
        header_idx = next((i for i, l in enumerate(lines) if not l.startswith("#")), 0)
        data_lines = lines[header_idx+1:]

        all_files = []
        
        for line in data_lines:
            parts = line.split(",")
            if len(parts) < 8:
                continue

            file_path = parts[0].strip()
            parameters = set(parts[7].strip().split())

            # Filter by organization if specified
            if org_prefix and not file_path.lower().startswith(org_prefix.lower()):
                continue

            # Check if any target parameters are present
            found = target_params.intersection(parameters)
            if not found:
                continue

            # Build full URL with dac/ prefix
            full_url = f"{self.config['base_url']}dac/{file_path}"
            filename = os.path.basename(file_path)
            
            all_files.append({
                "url": full_url,
                "filename": filename,
                "file_path": file_path,
                "parameters": list(found)
            })

            if len(all_files) >= self.config["max_total_files"]:
                break

        self.stats["found"] = len(all_files)
        LOG.info(f"Discovered {len(all_files)} BGC files with target parameters")
        return all_files

    def download_file(self, file_info: Dict[str, Any]) -> str:
        """Download a single BGC file."""
        url = file_info["url"]
        filename = file_info["filename"]
        dest = os.path.join(self.download_dir, filename)

        # Skip if already failed with 404
        if url in self.failed_urls:
            return None

        if self.config.get("skip_existing", True) and os.path.exists(dest):
            self.stats["skipped_existing"] += 1
            LOG.debug(f"Skipped (exists): {filename}")
            return dest

        attempts = 0
        max_retries = self.config.get("max_retries", 3)
        base_delay = self.config.get("retry_delay", 5)
        
        while attempts < max_retries:
            try:
                if attempts > 0:
                    delay = base_delay * (2 ** (attempts - 1)) + (time.time() % 1)
                    time.sleep(delay)
                
                r = requests.get(url, timeout=self.config.get("download_timeout", 120), stream=True)
                
                if r.status_code == 200:
                    with open(dest, "wb") as fh:
                        for chunk in r.iter_content(chunk_size=8192):
                            fh.write(chunk)
                    LOG.info(f"Downloaded: {filename}")
                    self.stats["downloaded"] += 1
                    return dest
                elif r.status_code == 404:
                    self.failed_urls.add(url)
                    self.stats["skipped_404"] += 1
                    LOG.warning(f"Not found (404): {filename}")
                    return None
                else:
                    LOG.warning(f"Bad response ({r.status_code}) for {url}")
            except Exception as e:
                LOG.warning(f"Download attempt {attempts + 1}/{max_retries} failed for {url}: {str(e)[:100]}")
            
            attempts += 1

        self.stats["errors"].append({"url": url, "error": "download_failed"})
        return None

    def run(self):
        """Main execution method."""
        files = self.discover_bgc_files()
        if not files:
            LOG.warning("No BGC files discovered. Exiting.")
            return

        LOG.info(f"Downloading {len(files)} BGC files")
        
        for i, f in enumerate(files, 1):
            try:
                self.download_file(f)
                
                if i % 100 == 0:
                    LOG.info(f"Progress: {i}/{len(files)} files processed")
            except Exception as e:
                LOG.error(f"Error downloading {f['filename']}: {e}")
                self.stats["errors"].append({"file": f["filename"], "error": str(e)})

        LOG.info("===== BGC DOWNLOAD SUMMARY =====")
        LOG.info(f"Files found: {self.stats['found']}")
        LOG.info(f"Files downloaded: {self.stats['downloaded']}")
        LOG.info(f"Files skipped (existing): {self.stats['skipped_existing']}")
        LOG.info(f"Files skipped (404): {self.stats['skipped_404']}")
        LOG.info(f"Errors: {len(self.stats['errors'])}")
        if self.stats['errors']:
            LOG.info(f"Error details: {json.dumps(self.stats['errors'][:10], indent=2)}")


DEFAULT_CONFIG = {
    "index_url": "https://data-argo.ifremer.fr/argo_bio-profile_index.txt",
    "base_url": "https://data-argo.ifremer.fr/",
    "target_params": ["DOXY", "CHLA", "NITRATE", "PH"],
    "organization_prefix": "",  # Set to "" to include all organizations, "incois/" for specific org
    "download_dir": "./data/bgc_downloads/",
    "log_dir": "./logs/",
    "max_total_files": 1000000,
    "download_timeout": 60,
    "max_retries": 2,
    "retry_delay": 5,
    "skip_existing": True,
}


def main_cli():
    parser = argparse.ArgumentParser(description="BGC-Argo file downloader (no database)")
    parser.add_argument("--config", "-c", help="Path to JSON config file", default=None)
    parser.add_argument("--org", "-o", help="Organization prefix filter (e.g., 'incois/')", default="")
    parser.add_argument("--max-files", "-m", type=int, help="Maximum files to download", default=1000000)
    parser.add_argument("--download-dir", "-d", help="Download directory", default="./data/bgc_downloads/")
    args = parser.parse_args()

    cfg = DEFAULT_CONFIG.copy()
    
    # Load config file if provided
    if args.config and os.path.exists(args.config):
        with open(args.config, "r") as fh:
            user_cfg = json.load(fh)
            cfg.update(user_cfg)
    
    # Override with command line args
    if args.org:
        cfg["organization_prefix"] = args.org
    if args.max_files:
        cfg["max_total_files"] = args.max_files
    if args.download_dir:
        cfg["download_dir"] = args.download_dir

    LOG.info(f"Download directory: {cfg['download_dir']}")
    LOG.info(f"Organization filter: {cfg['organization_prefix'] or 'ALL'}")
    LOG.info(f"Max files: {cfg['max_total_files']}")
    
    downloader = BGCArgoDownloader(cfg)
    downloader.run()


if __name__ == "__main__":
    main_cli()
