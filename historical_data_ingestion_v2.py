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

    def is_file_processed(self, filename: str) -> bool:
        """Check if a file has already been processed in the database."""
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM argo_profiles WHERE source_file = %s LIMIT 1", (filename,))
                return cur.fetchone() is not None
        finally:
            conn.close()

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
        """

        create_measurements = """
        CREATE TABLE IF NOT EXISTS argo_measurements (
            id BIGSERIAL PRIMARY KEY,
            global_profile_id BIGINT REFERENCES argo_profiles(global_profile_id) ON DELETE CASCADE,
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

        # All indexes for optimal query performance
        create_indexes = [
            # Primary indexes
            "CREATE INDEX IF NOT EXISTS idx_profiles_float_id ON argo_profiles(float_id);",
            "CREATE INDEX IF NOT EXISTS idx_meas_profile ON argo_measurements(global_profile_id);",
            
            # Spatial queries
            "CREATE INDEX IF NOT EXISTS idx_profiles_location ON argo_profiles(latitude, longitude);",
            "CREATE INDEX IF NOT EXISTS idx_measurements_location ON argo_measurements(latitude, longitude);",
            
            # Temporal queries
            "CREATE INDEX IF NOT EXISTS idx_profiles_datetime ON argo_profiles(datetime);",
            "CREATE INDEX IF NOT EXISTS idx_measurements_datetime ON argo_measurements(datetime);",
            
            # Depth/pressure queries
            "CREATE INDEX IF NOT EXISTS idx_measurements_pressure ON argo_measurements(pressure_adjusted);",
            
            # Temperature and salinity queries
            "CREATE INDEX IF NOT EXISTS idx_measurements_temp ON argo_measurements(temperature_adjusted);",
            "CREATE INDEX IF NOT EXISTS idx_measurements_salinity ON argo_measurements(salinity_adjusted);",
            
            # Float-specific queries
            "CREATE INDEX IF NOT EXISTS idx_profiles_cycle ON argo_profiles(cycle_number);",
            
            # Composite indexes for common query patterns
            "CREATE INDEX IF NOT EXISTS idx_measurements_location_pressure ON argo_measurements(latitude, longitude, pressure_adjusted);",
            "CREATE INDEX IF NOT EXISTS idx_measurements_temp_depth ON argo_measurements(temperature_adjusted, pressure_adjusted);",
            
            # Source file index for deduplication
            "CREATE INDEX IF NOT EXISTS idx_profiles_source_file ON argo_profiles(source_file);"
        ]

        conn = self._connect()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(create_profiles)
                    cur.execute(create_measurements)
                    
                    # Create all indexes
                    for idx_sql in create_indexes:
                        cur.execute(idx_sql)
        finally:
            conn.close()
        LOG.info("Ensured DB tables and indexes exist (argo_profiles, argo_measurements)")

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

        cols = ["global_profile_id", "level", "pressure_adjusted", "temperature_adjusted", "salinity_adjusted", "pressure_adjusted_qc", "temperature_adjusted_qc", "salinity_adjusted_qc", "latitude", "longitude", "datetime"]
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
    def __init__(self, config: Dict[str, Any], db_config: Dict[str, Any], region: str = None, year: str = None):
        self.config = config
        self.db_config = db_config
        self.region = region
        self.year = year

        # Region-specific directories if region is specified
        if region:
            self.download_dir = os.path.join(self.config["download_dir"], region)
        else:
            self.download_dir = self.config["download_dir"]

        # Make directories
        os.makedirs(self.download_dir, exist_ok=True)
        os.makedirs(self.config["log_dir"], exist_ok=True)

        # Logging file
        log_suffix = f"_{region}" if region else ""
        if year:
            log_suffix += f"_{year}"
        fh = logging.FileHandler(os.path.join(self.config["log_dir"], f"historical_ingest{log_suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"))
        fh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        LOG.addHandler(fh)

        # Instantiate processors
        # Pass download_dir as NetCDFProcessor's data_dir so it reads where we download files
        self.netcdf_processor = NetCDFProcessor(data_dir=self.download_dir, db_config=self.db_config)
        self.data_processor = ArgoDataProcessor(self.db_config)

        self.stats = {
            "region": region,
            "year": year,
            "found": 0,
            "downloaded": 0,
            "processed_files": 0,
            "profiles": 0,
            "measurements": 0,
            "errors": []
        }

    # ---------- discovery ----------
    def discover_historical_files(self) -> List[Dict[str, Any]]:
        region_str = self.region or 'all regions'
        year_str = self.year or 'all years'
        LOG.info(f"Discovering files on IFREMER for region: {region_str}, year: {year_str}...")
        all_files = []
        base = self.config["base_url"]

        # If region is specified, only process that region
        regions = [self.region] if self.region else self.config["regions"]
        
        # If year is specified, only process that year
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
        LOG.info(f"Discovered {len(files)} netcdf files for {region_str}, year: {year_str}")
        return files

    # ---------- download ----------
    def download_file(self, file_info: Dict[str, Any]) -> str:
        url = file_info["url"]
        filename = file_info["filename"]
        dest = os.path.join(self.download_dir, filename)

        if self.config.get("skip_existing", True) and os.path.exists(dest):
            LOG.info(f"Skip (exists): {filename}")
            return dest

        attempts = 0
        max_retries = self.config.get("max_retries", 3)
        base_delay = self.config.get("retry_delay", 5)
        
        while attempts < max_retries:
            try:
                # Add exponential backoff with jitter
                if attempts > 0:
                    delay = base_delay * (2 ** (attempts - 1)) + (time.time() % 1)  # Add jitter
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
                elif r.status_code == 500:
                    LOG.warning(f"Server error (500) for {url} - attempt {attempts + 1}/{max_retries}")
                elif r.status_code == 404:
                    LOG.warning(f"File not found (404) for {url} - skipping retries")
                    break  # Don't retry 404s
                else:
                    LOG.warning(f"Bad response ({r.status_code}) for {url}")
            except requests.exceptions.Timeout as e:
                LOG.warning(f"Timeout on attempt {attempts + 1}/{max_retries} for {url}")
            except requests.exceptions.ConnectionError as e:
                LOG.warning(f"Connection error on attempt {attempts + 1}/{max_retries} for {url}: {str(e)[:100]}")
            except Exception as e:
                LOG.warning(f"Download attempt {attempts + 1}/{max_retries} failed for {url}: {str(e)[:100]}")
            
            attempts += 1

        LOG.error(f"Failed to download {url} after {attempts} attempts")
        self.stats["errors"].append({"url": url, "error": "download_failed"})
        return None

    # ---------- processing ----------
    def process_file(self, filename: str):
        """
        Use NetCDFProcessor.process_single_file which expects to find `filename` in its data_dir.
        """
        # Check if file already processed in database
        if self.data_processor.is_file_processed(filename):
            LOG.info(f"Skip (already in DB): {filename}")
            return 0, 0
        
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

            # Optionally save to CSV
            if self.config.get("save_csv", False):
                self._save_to_csv(profiles_df, measurements_df, filename)

            self.stats["profiles"] += 0 if profiles_df is None else len(profiles_df)
            self.stats["measurements"] += 0 if measurements_df is None else len(measurements_df)
            self.stats["processed_files"] += 1
            LOG.info(f"Processed: {filename} -> profiles:{len(profiles_df)} measurements:{len(measurements_df)}")
            return len(profiles_df), len(measurements_df)
        except Exception as e:
            LOG.exception(f"Processing failed for {filename}: {e}")
            self.stats["errors"].append({"file": filename, "error": str(e)})
            return 0, 0

    def _save_to_csv(self, profiles_df: pd.DataFrame, measurements_df: pd.DataFrame, filename: str):
        """Save processed data to CSV files in the download directory."""
        try:
            # Save CSV files in the same directory as the downloaded NetCDF files
            csv_dir = self.download_dir
            base_name = os.path.splitext(filename)[0]
            
            if not profiles_df.empty:
                profiles_csv = os.path.join(csv_dir, f"{base_name}_profiles.csv")
                profiles_df.to_csv(profiles_csv, index=False)
            
            if not measurements_df.empty:
                measurements_csv = os.path.join(csv_dir, f"{base_name}_measurements.csv")
                measurements_df.to_csv(measurements_csv, index=False)
            
            LOG.debug(f"Saved CSV files for {filename}")
        except Exception as e:
            LOG.warning(f"Failed to save CSV for {filename}: {e}")

    # ---------- run ----------
    def run(self):
        """
        Main execution method - processes files sequentially.
        """
        files = self.discover_historical_files()
        if not files:
            LOG.warning("No files discovered. Exiting.")
            return

        # Limit files to max_total_files
        files = files[:self.config.get("max_total_files", 10000)]
        
        # Sequential processing
        LOG.info(f"Processing {len(files)} files sequentially")
        for f in files:
            local = self.download_file(f)
            if local:
                self.process_file(f["filename"])

        # Summary
        LOG.info("===== INGEST SUMMARY =====")
        LOG.info(json.dumps(self.stats, indent=2))


# -------------------------
# CLI / default config
# -------------------------
DEFAULT_CONFIG = {
    "base_url": "https://data-argo.ifremer.fr/geo/",  # Base URL without region
    "years": ["2025"],
    "months": ["01","02","03","04","05","06","07","08","09","10","11","12"],
    "regions": [
        "indian_ocean",
#       "atlantic_ocean",
#       "pacific_ocean",
    ],
    "download_dir": "./data/historical_downloads/",
    "log_dir": "./logs/",
    "file_extensions": [".nc"],
    "max_files_per_year": 500,
    "max_total_files": 2000,
    "download_timeout": 180,
    "max_retries": 5,  # Increased from 3 to 5
    "retry_delay": 10,  # Increased from 5 to 10 seconds base delay
    "skip_existing": True,
    "save_csv": False,  # Set to True if you want CSV backups
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



def process_region_year(region: str, year: str, config: Dict[str, Any], base_db_cfg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single region and year combination.
    
    Args:
        region: Ocean region name
        year: Year to process (e.g., "2023")
        config: Configuration dictionary
        base_db_cfg: Base database configuration
    
    Returns:
        Dictionary with processing statistics
    """
    LOG.info(f"\n{'='*60}")
    LOG.info(f"Starting ingestion for region: {region}, year: {year}")
    LOG.info(f"{'='*60}\n")
    
    # Create region and year-specific database config
    # Convert year to 2-digit format (e.g., "2023" -> "23")
    year_suffix = year[-2:]
    db_cfg = base_db_cfg.copy()
    db_cfg["database"] = f"argo_{region}_{year_suffix}"
    
    LOG.info(f"Using database: {db_cfg['database']}")
    
    # Create downloader for this region and year
    downloader = HistoricalArgoDownloader(config, db_cfg, region=region, year=year)
    
    # Run sequential processing
    downloader.run()
    
    LOG.info(f"\n{'='*60}")
    LOG.info(f"Completed ingestion for region: {region}, year: {year}")
    LOG.info(f"{'='*60}\n")
    
    return downloader.stats


def main_cli():
    parser = argparse.ArgumentParser(description="Historical Argo downloader + Postgres ingest")
    parser.add_argument("--config", "-c", help="Path to JSON config for downloader", default=None)
    parser.add_argument("--db-config", "-d", help="Path to JSON DB config", default=None)
    parser.add_argument("--region", "-r", help="Specific region to process (indian_ocean, atlantic_ocean, pacific_ocean). If not specified, processes all regions.", default=None)
    parser.add_argument("--year", "-y", help="Specific year to process (e.g., 2023). If not specified, processes all years.", default=None)
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
        base_db_cfg = load_db_config_from_env_or_file(args.db_config)
    except Exception as e:
        LOG.error(f"Database config error: {e}")
        sys.exit(1)

    # Determine regions and years to process
    if args.region:
        regions_to_process = [args.region]
    else:
        regions_to_process = cfg["regions"]
    
    if args.year:
        years_to_process = [args.year]
    else:
        years_to_process = cfg["years"]

    # Create all region/year combinations
    region_year_combinations = [(region, year) for region in regions_to_process for year in years_to_process]

    LOG.info(f"Processing regions: {regions_to_process}")
    LOG.info(f"Processing years: {years_to_process}")
    LOG.info(f"Total combinations: {len(region_year_combinations)}")
    
    # Process region/year combinations sequentially
    LOG.info(f"Processing {len(region_year_combinations)} region/year combinations sequentially")
    
    # Process each region/year combination sequentially
    for region, year in region_year_combinations:
        process_region_year(region, year, cfg, base_db_cfg)


if __name__ == "__main__":
    main_cli()