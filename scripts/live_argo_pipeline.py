#!/usr/bin/env python3
"""
Live Argo Data Pipeline for FloatChat
Real production system that downloads and processes actual Argo data
Monitors November 2024+ data and updates live database hourly
"""

import os
import sys
import json
import time
import logging
import argparse
import requests
import psycopg2
from datetime import datetime, timedelta
from pathlib import Path
from bs4 import BeautifulSoup

# Add parent directory to path to import our processing modules
sys.path.append(str(Path(__file__).parent.parent))

try:
    from process_netcdf_to_postgres import NetCDFProcessor
    from scripts.setup_live_database import get_live_db_config
except ImportError as e:
    print(f"Error importing processing modules: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

class LiveArgoAutomation:
    def __init__(self, config_file="scripts/live_pipeline_config.json"):
        self.config_file = config_file
        self.load_config()
        self.setup_logging()
        self.db_config = get_live_db_config()
        self.run_id = None
        
    def load_config(self):
        """Load live pipeline configuration"""
        default_config = {
            "base_url": "https://data-argo.ifremer.fr/geo/indian_ocean/",
            "download_dir": "./data/live_downloads/",
            "processed_data_dir": "./processed_data_live/",
            "log_dir": "./logs/",
            "years_to_monitor": ["2024"],
            "months_to_monitor": ["11", "12"],  # November, December 2024
            "file_extensions": [".nc"],
            "max_files_per_run": 10,
            "enable_database_import": True,
            "cleanup_old_files": True,
            "cleanup_days": 30,
            "download_timeout": 120,
            "max_retries": 3,
            "retry_delay": 5
        }
        
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        self.config = default_config
        
        # Create directories
        for dir_key in ["download_dir", "processed_data_dir", "log_dir"]:
            os.makedirs(self.config[dir_key], exist_ok=True)
    
    def setup_logging(self):
        """Setup comprehensive logging for the live pipeline"""
        log_file = os.path.join(
            self.config["log_dir"], 
            f"live_argo_pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("🌊 === Live Argo Pipeline Started ===")
        self.logger.info(f"Config: {json.dumps(self.config, indent=2)}")
    
    def log_automation_run(self, status="running", **kwargs):
        """Log automation run to database for monitoring"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            if status == "running":
                # Start new run
                cursor.execute("""
                    INSERT INTO automation_log (run_timestamp, status, data_source)
                    VALUES (NOW(), %s, %s) RETURNING id
                """, (status, f"IFREMER {'/'.join(self.config['years_to_monitor'])}"))
                
                self.run_id = cursor.fetchone()[0]
                conn.commit()
                
            elif self.run_id:
                # Update existing run
                update_fields = []
                update_values = []
                
                for key, value in kwargs.items():
                    update_fields.append(f"{key} = %s")
                    update_values.append(value)
                
                if update_fields:
                    update_fields.append("status = %s")
                    update_values.append(status)
                    update_values.append(self.run_id)
                    
                    cursor.execute(f"""
                        UPDATE automation_log 
                        SET {', '.join(update_fields)}
                        WHERE id = %s
                    """, update_values)
                    
                    conn.commit()
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error logging automation run: {e}")
    
    def discover_new_files(self):
        """Discover new NetCDF files from IFREMER server"""
        self.logger.info("🔍 Discovering new files from IFREMER Argo database...")
        
        new_files = []
        total_files_checked = 0
        
        try:
            # Get current date to check for new months automatically
            current_date = datetime.now()
            current_year = current_date.year
            current_month = current_date.month
            
            # Expand monitoring to include current and future months
            years_to_check = self.config["years_to_monitor"].copy()
            if str(current_year) not in years_to_check:
                years_to_check.append(str(current_year))
            
            for year in years_to_check:
                months_to_check = self.config["months_to_monitor"].copy()
                
                # If it's the current year, add current month if not already included
                if int(year) == current_year:
                    current_month_str = f"{current_month:02d}"
                    if current_month_str not in months_to_check:
                        months_to_check.append(current_month_str)
                        self.logger.info(f"📅 Auto-detected current month: {current_month_str}/{year}")
                
                for month in months_to_check:
                    if len(new_files) >= self.config["max_files_per_run"]:
                        break
                    
                    month_url = f"{self.config['base_url']}{year}/{month}/"
                    self.logger.info(f"📡 Checking {month_url}")
                    
                    try:
                        response = requests.get(month_url, timeout=30)
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.text, 'html.parser')
                            links = soup.find_all('a', href=True)
                            
                            month_files = []
                            for link in links:
                                href = link['href']
                                if any(href.endswith(ext) for ext in self.config["file_extensions"]):
                                    month_files.append(href)
                            
                            total_files_checked += len(month_files)
                            self.logger.info(f"📊 Found {len(month_files)} NetCDF files in {month}/{year}")
                            
                            # Check which files we don't have locally
                            for filename in month_files:
                                if len(new_files) >= self.config["max_files_per_run"]:
                                    break
                                
                                local_path = os.path.join(self.config["download_dir"], filename)
                                
                                # Check if file exists and get its size
                                file_url = month_url + filename
                                if not os.path.exists(local_path) or self._should_redownload(file_url, local_path):
                                    
                                    # Get file size from server
                                    try:
                                        head_response = requests.head(file_url, timeout=10)
                                        file_size = int(head_response.headers.get('content-length', 0))
                                        file_size_mb = file_size / (1024 * 1024)
                                    except:
                                        file_size_mb = 0
                                    
                                    new_files.append({
                                        'url': file_url,
                                        'filename': filename,
                                        'local_path': local_path,
                                        'year': year,
                                        'month': month,
                                        'size_mb': f"{file_size_mb:.1f}",
                                        'size_bytes': file_size
                                    })
                                    
                                    self.logger.info(f"🆕 New file: {filename} ({file_size_mb:.1f} MB)")
                        
                        else:
                            self.logger.warning(f"⚠️  Could not access {month_url} (Status: {response.status_code})")
                    
                    except Exception as e:
                        self.logger.error(f"❌ Error checking {month_url}: {e}")
        
        except Exception as e:
            self.logger.error(f"❌ Error in file discovery: {e}")
        
        self.logger.info(f"📊 Discovery complete: {len(new_files)} new files found from {total_files_checked} total files")
        self.log_automation_run("discovering", files_checked=total_files_checked)
        
        return new_files
    
    def _should_redownload(self, file_url, local_path):
        """Check if file should be redownloaded (size mismatch, etc.)"""
        if not os.path.exists(local_path):
            return True
        
        try:
            # Check if local file size matches server file size
            local_size = os.path.getsize(local_path)
            head_response = requests.head(file_url, timeout=10)
            server_size = int(head_response.headers.get('content-length', 0))
            
            return local_size != server_size
        except:
            return False
    
    def download_files(self, files_to_download):
        """Download new NetCDF files from IFREMER"""
        downloaded_files = []
        
        self.logger.info(f"⬇️  Starting download of {len(files_to_download)} files...")
        
        for i, file_info in enumerate(files_to_download, 1):
            try:
                self.logger.info(f"📥 [{i}/{len(files_to_download)}] Downloading {file_info['filename']} ({file_info['size_mb']} MB)")
                
                # Download with retries
                success = False
                for attempt in range(self.config["max_retries"]):
                    try:
                        response = requests.get(
                            file_info['url'], 
                            stream=True, 
                            timeout=self.config["download_timeout"]
                        )
                        response.raise_for_status()
                        
                        # Download to temporary file first
                        temp_path = file_info['local_path'] + '.tmp'
                        with open(temp_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                        
                        # Move to final location
                        os.rename(temp_path, file_info['local_path'])
                        
                        downloaded_files.append(file_info['local_path'])
                        self.logger.info(f"✅ Downloaded {file_info['filename']}")
                        success = True
                        break
                        
                    except Exception as e:
                        self.logger.warning(f"⚠️  Download attempt {attempt + 1} failed: {e}")
                        if attempt < self.config["max_retries"] - 1:
                            time.sleep(self.config["retry_delay"])
                
                if not success:
                    self.logger.error(f"❌ Failed to download {file_info['filename']} after {self.config['max_retries']} attempts")
                
            except Exception as e:
                self.logger.error(f"❌ Error downloading {file_info['filename']}: {e}")
        
        self.logger.info(f"📊 Download complete: {len(downloaded_files)}/{len(files_to_download)} files successful")
        self.log_automation_run("downloading", files_downloaded=len(downloaded_files))
        
        return downloaded_files
    
    def process_files(self, downloaded_files):
        """Process downloaded NetCDF files into PostgreSQL format"""
        if not downloaded_files:
            self.logger.info("No files to process")
            return 0, 0
        
        self.logger.info(f"🔄 Processing {len(downloaded_files)} files...")
        
        try:
            # Initialize processor with live download directory
            processor = NetCDFProcessor(self.config["download_dir"])
            
            # Process files
            profiles_df, measurements_df = processor.process_all_files()
            
            if profiles_df.empty:
                self.logger.warning("No data extracted from files")
                return 0, 0
            
            # Save processed data
            output_dir = processor.save_to_csv(profiles_df, measurements_df, self.config["processed_data_dir"])
            
            profiles_count = len(profiles_df)
            measurements_count = len(measurements_df)
            
            self.logger.info(f"📊 Processed {profiles_count} profiles and {measurements_count:,} measurements")
            
            # Import to live database
            if self.config["enable_database_import"]:
                self.import_to_live_database(output_dir, profiles_count, measurements_count)
            
            self.log_automation_run("processing", 
                                  files_processed=len(downloaded_files),
                                  profiles_added=profiles_count,
                                  measurements_added=measurements_count)
            
            return profiles_count, measurements_count
            
        except Exception as e:
            self.logger.error(f"❌ Error processing files: {e}")
            self.log_automation_run("error", error_message=str(e))
            return 0, 0
    
    def import_to_live_database(self, processed_data_dir, profiles_count, measurements_count):
        """Import processed data to live PostgreSQL database"""
        self.logger.info("💾 Importing data to live PostgreSQL database...")
        
        try:
            profiles_file = os.path.join(processed_data_dir, "argo_profiles.csv")
            measurements_file = os.path.join(processed_data_dir, "argo_measurements.csv")
            
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Import profiles (with conflict resolution)
            self.logger.info("📊 Importing profiles metadata...")
            with open(profiles_file, 'r') as f:
                cursor.copy_expert("""
                    COPY argo_profiles (global_profile_id, source_file, local_profile_id, float_id, 
                                      cycle_number, datetime, latitude, longitude, min_pressure, 
                                      max_pressure, measurement_count, project_name, institution, data_mode) 
                    FROM STDIN WITH CSV HEADER
                """, f)
            
            # Import measurements
            self.logger.info("📊 Importing oceanographic measurements...")
            with open(measurements_file, 'r') as f:
                cursor.copy_expert("""
                    COPY argo_measurements (global_profile_id, level, pressure, temperature, 
                                          salinity, latitude, longitude, datetime) 
                    FROM STDIN WITH CSV HEADER
                """, f)
            
            conn.commit()
            
            # Get updated counts
            cursor.execute("SELECT COUNT(*) FROM argo_profiles;")
            total_profiles = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM argo_measurements;")
            total_measurements = cursor.fetchone()[0]
            
            self.logger.info(f"✅ Data imported successfully!")
            self.logger.info(f"📊 Live database now contains:")
            self.logger.info(f"   • Total profiles: {total_profiles:,}")
            self.logger.info(f"   • Total measurements: {total_measurements:,}")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"❌ Database import error: {e}")
            raise
    
    def cleanup_old_files(self):
        """Clean up old downloaded files to save disk space"""
        if not self.config.get("cleanup_old_files", False):
            return
        
        try:
            cutoff_date = datetime.now() - timedelta(days=self.config["cleanup_days"])
            download_dir = Path(self.config["download_dir"])
            
            cleaned_count = 0
            cleaned_size = 0
            
            for file_path in download_dir.glob("*.nc"):
                if file_path.stat().st_mtime < cutoff_date.timestamp():
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    cleaned_count += 1
                    cleaned_size += file_size
            
            if cleaned_count > 0:
                cleaned_size_mb = cleaned_size / (1024 * 1024)
                self.logger.info(f"🧹 Cleaned up {cleaned_count} old files ({cleaned_size_mb:.1f} MB)")
                
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def run_live_pipeline(self):
        """Run the complete live automation pipeline"""
        start_time = time.time()
        
        try:
            self.log_automation_run("running")
            
            # Step 1: Discover new files
            new_files = self.discover_new_files()
            
            if not new_files:
                self.logger.info("📭 No new files found - database is up to date")
                self.log_automation_run("completed", duration_seconds=time.time() - start_time)
                return
            
            # Step 2: Download files
            downloaded_files = self.download_files(new_files)
            
            if not downloaded_files:
                self.logger.warning("⚠️  No files downloaded successfully")
                self.log_automation_run("completed", duration_seconds=time.time() - start_time)
                return
            
            # Step 3: Process files
            profiles_count, measurements_count = self.process_files(downloaded_files)
            
            # Step 4: Cleanup
            self.cleanup_old_files()
            
            # Summary
            duration = time.time() - start_time
            self.logger.info(f"🎉 Live pipeline completed successfully!")
            self.logger.info(f"⏱️  Duration: {duration:.2f} seconds")
            self.logger.info(f"📊 Results:")
            self.logger.info(f"   • Files downloaded: {len(downloaded_files)}")
            self.logger.info(f"   • Profiles added: {profiles_count:,}")
            self.logger.info(f"   • Measurements added: {measurements_count:,}")
            
            self.log_automation_run("completed", duration_seconds=duration)
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"❌ Live pipeline failed: {e}")
            self.log_automation_run("error", error_message=str(e), duration_seconds=duration)
            raise
        
        finally:
            self.logger.info("🌊 === Live Argo Pipeline Finished ===")
    
    def create_live_config(self):
        """Create a live configuration file"""
        live_config = {
            "base_url": "https://data-argo.ifremer.fr/geo/indian_ocean/",
            "download_dir": "./data/live_downloads/",
            "processed_data_dir": "./processed_data_live/",
            "log_dir": "./logs/",
            "years_to_monitor": ["2024"],
            "months_to_monitor": ["11", "12"],
            "file_extensions": [".nc"],
            "max_files_per_run": 10,
            "enable_database_import": True,
            "cleanup_old_files": True,
            "cleanup_days": 30,
            "download_timeout": 120,
            "max_retries": 3,
            "retry_delay": 5
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(live_config, f, indent=2)
        
        print(f"✅ Live configuration created at {self.config_file}")
        print("Edit this file to customize the live pipeline behavior")

def main():
    parser = argparse.ArgumentParser(description="Live Argo Data Automation Pipeline")
    parser.add_argument("--config", default="scripts/live_pipeline_config.json", 
                       help="Configuration file path")
    parser.add_argument("--create-config", action="store_true",
                       help="Create a live configuration file")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be done without actually doing it")
    
    args = parser.parse_args()
    
    pipeline = LiveArgoAutomation(args.config)
    
    if args.create_config:
        pipeline.create_live_config()
        return
    
    if args.dry_run:
        print("DRY RUN MODE - No actual downloads or processing")
        pipeline.config["enable_database_import"] = False
        # Just discover files
        new_files = pipeline.discover_new_files()
        print(f"Would process {len(new_files)} files")
        return
    
    pipeline.run_live_pipeline()

if __name__ == "__main__":
    main()