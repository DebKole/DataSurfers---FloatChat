#!/usr/bin/env python3
"""
Downloads BGC-Argo NetCDF files from IFREMER based on bio-profile index,
processes them with NetCDFProcessor, and inserts profiles + measurements 
into a single PostgreSQL database.
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

# DB helpers
import psycopg2
import psycopg2.extras
import pandas as pd

# Import NetCDFProcessor
try:
    from process_netcdf_to_postgres import NetCDFProcessor
except Exception:
    print("Warning: Could not import NetCDFProcessor from process_netcdf_to_postgres.py.")
    raise


LOG = logging.getLogger("bgc_ingest")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class ArgoBGCDataProcessor:
    """
    Handles insertion of BGC profile and measurement DataFrames into PostgreSQL.
    Creates tables if they do not exist and performs bulk inserts.
    """

    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self._ensure_database()
        self._ensure_tables()

    def is_file_processed(self, filename: str) -> bool:
        """Check if a file has already been processed in the database."""
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM argo_bgc_profiles WHERE source_file = %s LIMIT 1", (filename,))
                return cur.fetchone() is not None
        finally:
            conn.close()

    def _connect(self):
        return psycopg2.connect(**self.db_config)

    def _ensure_database(self):
        """Create the database if it doesn't exist."""
        db_name = self.db_config.get('database')
        
        default_config = self.db_config.copy()
        default_config['database'] = 'postgres'
        
        try:
            conn = psycopg2.connect(**default_config)
            conn.autocommit = True
            
            with conn.cursor() as cur:
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
        CREATE TABLE IF NOT EXISTS argo_bgc_profiles (
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
        """

        create_measurements = """
        CREATE TABLE IF NOT EXISTS argo_bgc_measurements (
            id BIGSERIAL PRIMARY KEY,
            global_profile_id BIGINT REFERENCES argo_bgc_profiles(global_profile_id) ON DELETE CASCADE,
            level INTEGER,
            pressure_adjusted DOUBLE PRECISION,
            temperature_adjusted DOUBLE PRECISION,
            salinity_adjusted DOUBLE PRECISION,
            pressure_adjusted_qc INTEGER,
            temperature_adjusted_qc INTEGER,
            salinity_adjusted_qc INTEGER,
            latitude DOUBLE PRECISION,
            longitude DOUBLE PRECISION,
            datetime TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
        );
        """

        create_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_bgc_profiles_float_id ON argo_bgc_profiles(float_id);",
            "CREATE INDEX IF NOT EXISTS idx_bgc_meas_profile ON argo_bgc_measurements(global_profile_id);",
            "CREATE INDEX IF NOT EXISTS idx_bgc_profiles_location ON argo_bgc_profiles(latitude, longitude);",
            "CREATE INDEX IF NOT EXISTS idx_bgc_measurements_location ON argo_bgc_measurements(latitude, longitude);",
            "CREATE INDEX IF NOT EXISTS idx_bgc_profiles_datetime ON argo_bgc_profiles(datetime);",
            "CREATE INDEX IF NOT EXISTS idx_bgc_measurements_datetime ON argo_bgc_measurements(datetime);",
            "CREATE INDEX IF NOT EXISTS idx_bgc_measurements_pressure ON argo_bgc_measurements(pressure_adjusted);",
            "CREATE INDEX IF NOT EXISTS idx_bgc_measurements_temp ON argo_bgc_measurements(temperature_adjusted);",
            "CREATE INDEX IF NOT EXISTS idx_bgc_measurements_salinity ON argo_bgc_measurements(salinity_adjusted);",
            "CREATE INDEX IF NOT EXISTS idx_bgc_profiles_cycle ON argo_bgc_profiles(cycle_number);",
            "CREATE INDEX IF NOT EXISTS idx_bgc_profiles_source_file ON argo_bgc_profiles(source_file);"
        ]

        conn = self._connect()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(create_profiles)
                    cur.execute(create_measurements)
                    
                    for idx_sql in create_indexes:
                        cur.execute(idx_sql)
        finally:
            conn.close()
        LOG.info("Ensured DB tables and indexes exist (argo_bgc_profiles, argo_bgc_measurements)")

    def insert_profiles(self, profiles_df: pd.DataFrame, chunk_size: int = 1000):
        """Bulk insert profiles dataframe (upsert on primary key)."""
        if profiles_df is None or profiles_df.empty:
            return

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
                    insert_query = f"""
                    INSERT INTO argo_bgc_profiles ({', '.join(cols)})
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
        LOG.info(f"Inserted/updated {len(profiles_df)} profile records into argo_bgc_profiles")

    def insert_measurements(self, measurements_df: pd.DataFrame, chunk_size: int = 5000):
        """Bulk insert measurement rows."""
        if measurements_df is None or measurements_df.empty:
            return

        if "datetime" in measurements_df.columns:
            measurements_df = measurements_df.copy()
            measurements_df["datetime"] = pd.to_datetime(measurements_df["datetime"], errors="coerce")

        cols = ["global_profile_id", "level", "pressure_adjusted", "temperature_adjusted", 
                "salinity_adjusted", "pressure_adjusted_qc", "temperature_adjusted_qc", 
                "salinity_adjusted_qc", "latitude", "longitude", "datetime"]
        measurements_df = measurements_df[[c for c in cols if c in measurements_df.columns]]

        conn = self._connect()
        try:
            with conn:
                with conn.cursor() as cur:
                    insert_query = f"""
                    INSERT INTO argo_bgc_measurements ({', '.join(cols)})
                    VALUES %s
                    """
                    values = [tuple(row[col] if col in row.index else None for col in cols)
                              for _, row in measurements_df.iterrows()]
                    psycopg2.extras.execute_values(cur, insert_query, values, page_size=chunk_size)
        finally:
            conn.close()
        LOG.info(f"Inserted {len(measurements_df)} measurement records into argo_bgc_measurements")


class BGCArgoDownloader:
    """Downloads and processes BGC-Argo files based on bio-profile index."""
    
    def __init__(self, config: Dict[str, Any], db_config: Dict[str, Any]):
        self.config = config
        self.db_config = db_config
        self.download_dir = config["download_dir"]
        
        os.makedirs(self.download_dir, exist_ok=True)
        os.makedirs(config["log_dir"], exist_ok=True)

        # Setup logging
        fh = logging.FileHandler(os.path.join(config["log_dir"], 
                                              f"bgc_ingest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"))
        fh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        LOG.addHandler(fh)

        # Instantiate processors
        self.netcdf_processor = NetCDFProcessor(data_dir=self.download_dir, db_config=self.db_config)
        self.data_processor = ArgoBGCDataProcessor(self.db_config)

        self.stats = {
            "found": 0,
            "downloaded": 0,
            "processed_files": 0,
            "profiles": 0,
            "measurements": 0,
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
                    return None
                else:
                    LOG.warning(f"Bad response ({r.status_code}) for {url}")
            except Exception as e:
                LOG.warning(f"Download attempt {attempts + 1}/{max_retries} failed for {url}: {str(e)[:100]}")
            
            attempts += 1

        self.stats["errors"].append({"url": url, "error": "download_failed"})
        return None

    def process_file(self, filename: str):
        """Process a single BGC NetCDF file."""
        if self.data_processor.is_file_processed(filename):
            LOG.info(f"Skip (already in DB): {filename}")
            return 0, 0
        
        try:
            profiles_df, measurements_df = self.netcdf_processor.process_single_file(filename)
            if profiles_df is None or measurements_df is None:
                LOG.warning(f"No data extracted from {filename}")
                return 0, 0

            if not profiles_df.empty:
                self.data_processor.insert_profiles(profiles_df)
            if not measurements_df.empty:
                self.data_processor.insert_measurements(measurements_df)

            self.stats["profiles"] += len(profiles_df) if profiles_df is not None else 0
            self.stats["measurements"] += len(measurements_df) if measurements_df is not None else 0
            self.stats["processed_files"] += 1
            LOG.info(f"Processed: {filename} -> profiles:{len(profiles_df)} measurements:{len(measurements_df)}")
            return len(profiles_df), len(measurements_df)
        except Exception as e:
            LOG.exception(f"Processing failed for {filename}: {e}")
            self.stats["errors"].append({"file": filename, "error": str(e)})
            return 0, 0

    def run(self):
        """Main execution method."""
        files = self.discover_bgc_files()
        if not files:
            LOG.warning("No BGC files discovered. Exiting.")
            return

        LOG.info(f"Processing {len(files)} BGC files sequentially")
        
        for i, f in enumerate(files, 1):
            try:
                local = self.download_file(f)
                if local:
                    self.process_file(f["filename"])
                
                if i % 100 == 0:
                    LOG.info(f"Progress: {i}/{len(files)} files processed")
            except Exception as e:
                LOG.error(f"Error processing {f['filename']}: {e}")
                self.stats["errors"].append({"file": f["filename"], "error": str(e)})

        LOG.info("===== BGC INGEST SUMMARY =====")
        LOG.info(json.dumps(self.stats, indent=2))


DEFAULT_CONFIG = {
    "index_url": "https://data-argo.ifremer.fr/argo_bio-profile_index.txt",
    "base_url": "https://data-argo.ifremer.fr/",
    "target_params": ["DOXY", "CHLA", "NITRATE", "PH"],
    "organization_prefix": "",  # Set to None or "" to include all organizations, "incois/" for specific org
    "download_dir": "./data/bgc_downloads/",
    "log_dir": "./logs/",
    "max_total_files": 1000000,
    "download_timeout": 60,
    "max_retries": 2,
    "retry_delay": 5,
    "skip_existing": True,
}


def load_db_config_from_env_or_file(cfg_path: str = None):
    """Load database config from JSON file or environment variables."""
    if cfg_path and os.path.exists(cfg_path):
        with open(cfg_path, "r") as fh:
            cfg = json.load(fh)
        return {
            "host": cfg.get("host", "localhost"),
            "port": int(cfg.get("port", 5432)),
            "user": cfg.get("user", "postgres"),
            "password": cfg.get("password"),
            "database": cfg.get("database") or cfg.get("dbname") or "argo_bgc"
        }

    host = os.getenv("DB_HOST", "localhost")
    port = int(os.getenv("DB_PORT", 5432))
    user = os.getenv("DB_USERNAME", "postgres")
    password = os.getenv("DB_PASSWORD")
    database = os.getenv("DB_NAME", "argo_bgc")

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
    parser = argparse.ArgumentParser(description="BGC-Argo downloader + Postgres ingest")
    parser.add_argument("--config", "-c", help="Path to JSON config for downloader", default=None)
    parser.add_argument("--db-config", "-d", help="Path to JSON DB config", default=None)
    args = parser.parse_args()

    cfg = DEFAULT_CONFIG.copy()
    if args.config and os.path.exists(args.config):
        with open(args.config, "r") as fh:
            user_cfg = json.load(fh)
            cfg.update(user_cfg)

    try:
        db_cfg = load_db_config_from_env_or_file(args.db_config)
    except Exception as e:
        LOG.error(f"Database config error: {e}")
        sys.exit(1)

    LOG.info(f"Using database: {db_cfg['database']}")
    
    downloader = BGCArgoDownloader(cfg, db_cfg)
    downloader.run()


if __name__ == "__main__":
    main_cli()