#!/usr/bin/env python3
"""
Downloads Argo NetCDF files (2019-2024) from IFREMER.
NO DATABASE INGESTION - ONLY DOWNLOADS FILES.
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
from bs4 import BeautifulSoup


LOG = logging.getLogger("historical_download")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class HistoricalArgoDownloader:
    def __init__(self, config: Dict[str, Any], region: str = None, year: str = None):
        self.config = config
        self.region = region
        self.year = year

        # Region directory
        if region:
            self.download_dir = os.path.join(self.config["download_dir"], region)
        else:
            self.download_dir = self.config["download_dir"]

        os.makedirs(self.download_dir, exist_ok=True)
        os.makedirs(self.config["log_dir"], exist_ok=True)

        # Setup file logger
        log_suffix = f"_{region}" if region else ""
        if year:
            log_suffix += f"_{year}"
        log_file = f"historical_download{log_suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        fh = logging.FileHandler(os.path.join(self.config["log_dir"], log_file))
        fh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        LOG.addHandler(fh)

        self.stats = {
            "region": region,
            "year": year,
            "found": 0,
            "downloaded": 0,
            "skipped_existing": 0,
            "errors": []
        }

    # ---------- discovery ----------
    def discover_historical_files(self) -> List[Dict[str, Any]]:
        region_str = self.region or "all regions"
        year_str = self.year or "all years"
        LOG.info(f"Discovering files on IFREMER for region: {region_str}, year: {year_str}...")

        all_files = []
        base = self.config["base_url"]

        # Pick specific region/year
        regions = [self.region] if self.region else self.config["regions"]
        years = [self.year] if self.year else self.config["years"]

        for region in regions:
            region_url = f"{base}{region}/"
            for year in years:
                if len(all_files) >= self.config["max_total_files"]:
                    break
                for month in self.config["months"]:
                    if len(all_files) >= self.config["max_total_files"]:
                        break

                    month_url = f"{region_url}{year}/{month}/"
                    try:
                        r = requests.get(month_url, timeout=15)
                        if r.status_code != 200:
                            continue

                        soup = BeautifulSoup(r.text, "html.parser")
                        for a in soup.find_all("a", href=True):
                            href = a["href"]
                            if any(href.endswith(ext) for ext in self.config["file_extensions"]):
                                full_url = month_url + href
                                all_files.append({
                                    "url": full_url,
                                    "filename": href,
                                    "year": year,
                                    "month": month,
                                    "region": region
                                })
                    except Exception as e:
                        LOG.warning(f"Failed to list {month_url}: {e}")

        # Deduplicate + limit
        unique = {f["url"]: f for f in all_files}
        files = list(unique.values())[: self.config["max_total_files"]]

        self.stats["found"] = len(files)
        LOG.info(f"Discovered {len(files)} NetCDF files.")
        return files

    # ---------- download ----------
    def download_file(self, file_info: Dict[str, Any]) -> str:
        url = file_info["url"]
        filename = file_info["filename"]
        dest = os.path.join(self.download_dir, filename)

        # Skip existing
        if self.config.get("skip_existing", True) and os.path.exists(dest):
            self.stats["skipped_existing"] += 1
            return dest

        attempts = 0
        max_retries = self.config.get("max_retries", 3)
        base_delay = self.config.get("retry_delay", 5)

        while attempts < max_retries:
            try:
                if attempts > 0:
                    delay = base_delay * (2 ** (attempts - 1)) + (time.time() % 1)
                    LOG.info(f"Retry {attempts}/{max_retries} for {filename} after {delay:.1f}s delay")
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
                    LOG.warning(f"File not found (404): {url}")
                    break

                else:
                    LOG.warning(f"Bad response ({r.status_code}) for {url}")

            except Exception as e:
                LOG.warning(f"Error downloading {url}: {e}")

            attempts += 1

        LOG.error(f"Failed to download {url} after {attempts} attempts")
        self.stats["errors"].append({"url": url, "error": "download_failed"})
        return None

    # ---------- run ----------
    def run(self):
        files = self.discover_historical_files()
        if not files:
            LOG.warning("No files discovered. Exiting.")
            return

        files = files[: self.config.get("max_total_files", 10000)]

        LOG.info(f"Downloading {len(files)} files")

        for i, f in enumerate(files, 1):
            self.download_file(f)

            if i % 100 == 0:
                LOG.info(f"Progress: {i}/{len(files)} files processed")

        LOG.info("===== DOWNLOAD SUMMARY =====")
        LOG.info(f"Files found: {self.stats['found']}")
        LOG.info(f"Files downloaded: {self.stats['downloaded']}")
        LOG.info(f"Skipped existing: {self.stats['skipped_existing']}")
        LOG.info(f"Errors: {len(self.stats['errors'])}")


# -------------------------
# DEFAULT CONFIG (same as before)
# -------------------------
DEFAULT_CONFIG = {
    "base_url": "https://data-argo.ifremer.fr/geo/",
    "years": ["2025","2024","2023","2022","2021"],
    "months": ["01","02","03","04","05","06","07","08","09","10","11","12"],
    "regions": ["indian_ocean"],
    "download_dir": "./data/historical_downloads/",
    "log_dir": "./logs/",
    "file_extensions": [".nc"],
    "max_total_files": 2000,
    "download_timeout": 180,
    "max_retries": 5,
    "retry_delay": 10,
    "skip_existing": True,
}


def process_region_year(region: str, year: str, config: Dict[str, Any]):
    LOG.info(f"\n{'='*60}")
    LOG.info(f"Starting download for region: {region}, year: {year}")
    LOG.info(f"{'='*60}\n")

    downloader = HistoricalArgoDownloader(config, region=region, year=year)
    downloader.run()

    LOG.info(f"\n{'='*60}")
    LOG.info(f"Completed: region={region}, year={year}")
    LOG.info(f"{'='*60}\n")

    return downloader.stats


def main_cli():
    parser = argparse.ArgumentParser(description="Historical Argo NetCDF Downloader (NO DATABASE)")
    parser.add_argument("--config", "-c", help="Path to JSON config", default=None)
    parser.add_argument("--region", "-r", help="Specific region (optional)", default=None)
    parser.add_argument("--year", "-y", help="Specific year (optional)", default=None)
    args = parser.parse_args()

    cfg = DEFAULT_CONFIG.copy()
    if args.config:
        if os.path.exists(args.config):
            with open(args.config, "r") as fh:
                cfg.update(json.load(fh))
        else:
            LOG.warning("Config file not found; using defaults.")

    regions_to_process = [args.region] if args.region else cfg["regions"]
    years_to_process = [args.year] if args.year else cfg["years"]

    LOG.info(f"Processing regions: {regions_to_process}")
    LOG.info(f"Processing years: {years_to_process}")

    for region in regions_to_process:
        for year in years_to_process:
            process_region_year(region, year, cfg)


if __name__ == "__main__":
    main_cli()
