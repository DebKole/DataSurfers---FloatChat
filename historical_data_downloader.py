#!/usr/bin/env python3
"""
Downloads Argo NetCDF files (2019-2024) from IFREMER, processes them with NetCDFProcessor,
and inserts profiles + measurements into PostgreSQL via ArgoDataProcessor.
"""

import os
import sys
import json
import time
import logging
import argparse
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv
load_dotenv()
import requests
from bs4 import BeautifulSoup

# DB helpers
import psycopg2
import psycopg2.extras
import pandas as pd

# Try to import user's NetCDFProcessor (the class you pasted). If it's not importable,
# you'll want to save your class in process_netcdf_to_postgres.py and import from there.
try:
    from process_netcdf_to_postgres import NetCDFProcessor
except Exception:
    # Fallback: if your NetCDFProcessor class is not in a module, you can paste it here.
    # For brevity we assume the class you provided is in process_netcdf_to_postgres.py
    print("Warning: Could not import NetCDFProcessor from process_netcdf_to_postgres.py. "
          "Make sure that file exists and contains the NetCDFProcessor class.")
    raise


LOG = logging.getLogger("historical_ingest")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class ArgoDataProcessor:
    """
    Handles insertion of profile and measurement DataFrames into PostgreSQL.
    Creates tables if they do not exist and performs bulk inserts.
    """

    def __init__(self, db_config: Dict[str, Any]):
        """
        db_config: dict with keys 'host','port','dbname','user','password'
        """
        self.db_config = db_config
        self._ensure_database()
        self._ensure_tables()

    def _connect(self):
        return psycopg2.connect(**self.db_config)

    def _ensure_database(self):
        """Create the database if it doesn't exist."""
        db_name = self.db_config.get('database')
        
        # Connect to default 'postgres' database to check/create target database
        default_config = self.db_config.copy()
        default_config['database'] = 'postgres'
        
        try:
            conn = psycopg2.connect(**default_config)
            conn.autocommit = True  # Required for CREATE DATABASE
            
            with conn.cursor() as cur:
                # Check if database exists
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
                exists = cur.fetchone()
                
                if not exists:
                    LOG.info(f"Database '{db_name}' does not exist. Creating it...")
                    cur.execute(f'CREATE DATABASE "{db_name}"')
                    LOG.info(f"Database '{db_name}' created successfully")
                else:
                    LOG.info(f"Database '{db_name}' already exists")
            
            conn.close()
        except Exception as e:
            LOG.error(f"Error ensuring database exists: {e}")
            raise

    def _ensure_tables(self):
        """Create tables with appropriate schema if not exists."""
        create_profiles = """
        CREATE TABLE IF NOT EXISTS argo_profiles (
            global_profile_id BIGINT PRIMARY KEY,
            source_file TEXT,
            local_profile_id INTEGER,
            float_id TEXT,
            cycle_number INTEGER,
            datetime TIMESTAMP WITH TIME ZONE,
            latitude DOUBLE PRECISION,
            longitude DOUBLE PRECISION,
            min_pressure DOUBLE PRECISION,
            max_pressure DOUBLE PRECISION,
            measurement_count INTEGER,
            project_name TEXT,
            institution TEXT,
            data_mode TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_profiles_float_id ON argo_profiles(float_id);
        """

        create_measurements = """
        CREATE TABLE IF NOT EXISTS argo_measurements (
            id BIGSERIAL PRIMARY KEY,
            global_profile_id BIGINT REFERENCES argo_profiles(global_profile_id) ON DELETE CASCADE,
            level INTEGER,
            pressure DOUBLE PRECISION,
            temperature DOUBLE PRECISION,
            salinity DOUBLE PRECISION,
            latitude DOUBLE PRECISION,
            longitude DOUBLE PRECISION,
            datetime TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_meas_profile ON argo_measurements(global_profile_id);
        """

        conn = self._connect()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(create_profiles)
                    cur.execute(create_measurements)
        finally:
            conn.close()
        LOG.info("Ensured DB tables exist (argo_profiles, argo_measurements)")

    def insert_profiles(self, profiles_df: pd.DataFrame, chunk_size: int = 1000):
        """Bulk insert profiles dataframe (upsert on primary key)."""
        if profiles_df is None or profiles_df.empty:
            return

        # Ensure datetime column is proper datetime or None
        if "datetime" in profiles_df.columns:
            profiles_df = profiles_df.copy()
            profiles_df["datetime"] = pd.to_datetime(profiles_df["datetime"], errors="coerce")

        cols = [
            "global_profile_id", "source_file", "local_profile_id", "float_id",
            "cycle_number", "datetime", "latitude", "longitude", "min_pressure",
            "max_pressure", "measurement_count", "project_name", "institution", "data_mode"
        ]
        profiles_df = profiles_df[[c for c in cols if c in profiles_df.columns]]

        conn = self._connect()
        try:
            with conn:
                with conn.cursor() as cur:
                    # Using execute_values for performance
                    insert_query = f"""
                    INSERT INTO argo_profiles ({', '.join(cols)})
                    VALUES %s
                    ON CONFLICT (global_profile_id) DO UPDATE SET
                        source_file = EXCLUDED.source_file,
                        local_profile_id = EXCLUDED.local_profile_id,
                        float_id = EXCLUDED.float_id,
                        cycle_number = EXCLUDED.cycle_number,
                        datetime = EXCLUDED.datetime,
                        latitude = EXCLUDED.latitude,
                        longitude = EXCLUDED.longitude,
                        min_pressure = EXCLUDED.min_pressure,
                        max_pressure = EXCLUDED.max_pressure,
                        measurement_count = EXCLUDED.measurement_count,
                        project_name = EXCLUDED.project_name,
                        institution = EXCLUDED.institution,
                        data_mode = EXCLUDED.data_mode;
                    """

                    values = [
                        tuple(row[col] if col in row.index else None for col in cols)
                        for _, row in profiles_df.iterrows()
                    ]
                    psycopg2.extras.execute_values(cur, insert_query, values, page_size=chunk_size)
        finally:
            conn.close()
        LOG.info(f"Inserted/updated {len(profiles_df)} profile records into argo_profiles")

    def insert_measurements(self, measurements_df: pd.DataFrame, chunk_size: int = 5000):
        """Bulk insert measurement rows. No upsert — duplicates may be avoided by cleaning upstream."""
        if measurements_df is None or measurements_df.empty:
            return

        if "datetime" in measurements_df.columns:
            measurements_df = measurements_df.copy()
            measurements_df["datetime"] = pd.to_datetime(measurements_df["datetime"], errors="coerce")

        cols = ["global_profile_id", "level", "pressure", "temperature", "salinity", "latitude", "longitude", "datetime"]
        measurements_df = measurements_df[[c for c in cols if c in measurements_df.columns]]

        conn = self._connect()
        try:
            with conn:
                with conn.cursor() as cur:
                    insert_query = f"""
                    INSERT INTO argo_measurements ({', '.join(cols)})
                    VALUES %s
                    """
                    values = [tuple(row[col] if col in row.index else None for col in cols)
                              for _, row in measurements_df.iterrows()]
                    psycopg2.extras.execute_values(cur, insert_query, values, page_size=chunk_size)
        finally:
            conn.close()
        LOG.info(f"Inserted {len(measurements_df)} measurement records into argo_measurements")


class HistoricalArgoDownloader:
    def __init__(self, config: Dict[str, Any], db_config: Dict[str, Any]):
        self.config = config
        self.db_config = db_config

        # Make directories
        os.makedirs(self.config["download_dir"], exist_ok=True)
        os.makedirs(self.config["log_dir"], exist_ok=True)
        os.makedirs(self.config["processed_data_dir"], exist_ok=True)

        # Logging file
        fh = logging.FileHandler(os.path.join(self.config["log_dir"], f"historical_ingest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"))
        fh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        LOG.addHandler(fh)

        # Instantiate processors
        # Pass download_dir as NetCDFProcessor's data_dir so it reads where we download files
        self.netcdf_processor = NetCDFProcessor(data_dir=self.config["download_dir"], db_config=self.db_config)
        self.data_processor = ArgoDataProcessor(self.db_config)

        self.stats = {
            "found": 0,
            "downloaded": 0,
            "processed_files": 0,
            "profiles": 0,
            "measurements": 0,
            "errors": []
        }

    # ---------- discovery ----------
    def discover_historical_files(self) -> List[Dict[str, Any]]:
        LOG.info("Discovering files on IFREMER...")
        all_files = []
        base = self.config["base_url"]

        for region in self.config["regions"]:
            region_url = base.replace("indian_ocean", region)
            for year in self.config["years"]:
                if len(all_files) >= self.config["max_total_files"]:
                    break
                for month in self.config["months"]:
                    if len(all_files) >= self.config["max_total_files"]:
                        break
                    month_url = f"{region_url}{year}/{month}/"
                    try:
                        r = requests.get(month_url, timeout=15)
                        if r.status_code != 200:
                            LOG.debug(f"{month_url} returned {r.status_code}")
                            continue
                        soup = BeautifulSoup(r.text, "html.parser")
                        links = soup.find_all("a", href=True)
                        for a in links:
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

        # deduplicate by url
        unique = {f["url"]: f for f in all_files}
        files = list(unique.values())[: self.config["max_total_files"]]
        self.stats["found"] = len(files)
        LOG.info(f"Discovered {len(files)} netcdf files")
        return files

    # ---------- download ----------
    def download_file(self, file_info: Dict[str, Any]) -> str:
        url = file_info["url"]
        filename = file_info["filename"]
        dest = os.path.join(self.config["download_dir"], filename)

        if self.config.get("skip_existing", True) and os.path.exists(dest):
            LOG.info(f"Skip (exists): {filename}")
            return dest

        attempts = 0
        while attempts < self.config.get("max_retries", 3):
            try:
                r = requests.get(url, timeout=self.config.get("download_timeout", 120))
                if r.status_code == 200:
                    with open(dest, "wb") as fh:
                        fh.write(r.content)
                    LOG.info(f"Downloaded: {filename}")
                    self.stats["downloaded"] += 1
                    return dest
                else:
                    LOG.warning(f"Bad response ({r.status_code}) for {url}")
            except Exception as e:
                LOG.warning(f"Download attempt failed for {url}: {e}")
            attempts += 1
            time.sleep(self.config.get("retry_delay", 5))

        LOG.error(f"Failed to download {url} after {attempts} attempts")
        self.stats["errors"].append({"url": url, "error": "download_failed"})
        return None

    # ---------- processing ----------
    def process_file(self, filename: str):
        """
        Use NetCDFProcessor.process_single_file which expects to find `filename` in its data_dir.
        """
        try:
            profiles_df, measurements_df = self.netcdf_processor.process_single_file(filename)
            if profiles_df is None or measurements_df is None:
                LOG.warning(f"No data extracted from {filename}")
                return 0, 0

            # Insert into Postgres
            if not profiles_df.empty:
                self.data_processor.insert_profiles(profiles_df)
            if not measurements_df.empty:
                self.data_processor.insert_measurements(measurements_df)

            self.stats["profiles"] += 0 if profiles_df is None else len(profiles_df)
            self.stats["measurements"] += 0 if measurements_df is None else len(measurements_df)
            self.stats["processed_files"] += 1
            LOG.info(f"Processed: {filename} -> profiles:{len(profiles_df)} measurements:{len(measurements_df)}")
            return len(profiles_df), len(measurements_df)
        except Exception as e:
            LOG.exception(f"Processing failed for {filename}: {e}")
            self.stats["errors"].append({"file": filename, "error": str(e)})
            return 0, 0

    # ---------- run ----------
    def run(self):
        files = self.discover_historical_files()
        if not files:
            LOG.warning("No files discovered. Exiting.")
            return

        # Optionally prioritize months or sample; here we just iterate discovered list
        for f in files:
            # Respect overall max_total_files and per-year limit if set
            if self.stats["downloaded"] >= self.config.get("max_total_files", 10000):
                LOG.info("Reached max_total_files limit")
                break

            # Download then process
            local = self.download_file(f)
            if local:
                # pass only the filename to NetCDFProcessor.process_single_file
                self.process_file(f["filename"])

        # Summary
        LOG.info("===== INGEST SUMMARY =====")
        LOG.info(json.dumps(self.stats, indent=2))


# -------------------------
# CLI / default config
# -------------------------
DEFAULT_CONFIG = {
    "base_url": "https://data-argo.ifremer.fr/geo/indian_ocean/",
    "years": ["2019", "2020", "2021", "2022", "2023", "2024"],
    "months": ["01","02","03","04","05","06","07","08","09","10","11","12"],
    "regions": ["indian_ocean"],
    "download_dir": "./data/historical_downloads/",
    "processed_data_dir": "./processed_data_historical/",
    "log_dir": "./logs/",
    "file_extensions": [".nc"],
    "max_files_per_year": 500,
    "max_total_files": 2000,
    "download_timeout": 180,
    "max_retries": 3,
    "retry_delay": 5,
    "skip_existing": True
}


def load_db_config_from_env_or_file(cfg_path: str = None):
    """
    Loads database config from:
      1) JSON file if cfg_path provided
      2) Environment variables (DB_HOST, DB_PORT, DB_USERNAME, DB_PASSWORD, DB_NAME)

    Matches the structure:
    {
        'host': ...,
        'port': ...,
        'user': ...,
        'password': ...,
        'database': ...
    }
    """
    # 1) JSON config file (highest priority)
    if cfg_path and os.path.exists(cfg_path):
        with open(cfg_path, "r") as fh:
            cfg = json.load(fh)

        # Normalize JSON keys to match output
        return {
            "host": cfg.get("host", "localhost"),
            "port": int(cfg.get("port", 5432)),
            "user": cfg.get("user", "postgres"),
            "password": cfg.get("password"),
            "database": cfg.get("database") or cfg.get("dbname") or "floatchat_argo"
        }

    # 2) Environment variables
    host = os.getenv("DB_HOST", "localhost")
    port = int(os.getenv("DB_PORT", 5432))
    user = os.getenv("DB_USERNAME", "postgres")
    password = os.getenv("DB_PASSWORD")
    database = os.getenv("DB_NAME", "floatchat_argo_prev")

    # Ensure required fields exist
    if password is None:
        raise RuntimeError("DB_PASSWORD missing in environment or config file.")

    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "database": database
    }



def main_cli():
    parser = argparse.ArgumentParser(description="Historical Argo downloader + Postgres ingest")
    parser.add_argument("--config", "-c", help="Path to JSON config for downloader", default=None)
    parser.add_argument("--db-config", "-d", help="Path to JSON DB config", default=None)
    args = parser.parse_args()

    cfg = DEFAULT_CONFIG.copy()
    if args.config:
        if os.path.exists(args.config):
            with open(args.config, "r") as fh:
                user_cfg = json.load(fh)
                cfg.update(user_cfg)
        else:
            LOG.warning("Config file path provided but not found; using defaults.")

    try:
        db_cfg = load_db_config_from_env_or_file(args.db_config)
    except Exception as e:
        LOG.error(f"Database config error: {e}")
        sys.exit(1)

    downloader = HistoricalArgoDownloader(cfg, db_cfg)
    downloader.run()


if __name__ == "__main__":
    main_cli()
