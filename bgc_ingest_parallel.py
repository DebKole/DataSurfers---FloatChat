#!/usr/bin/env python3
"""
Parallel BGC-Argo data ingestion using multiprocessing
Optimized for macOS with 10 workers
Moves successfully ingested files to 'ingested_bgc' folder
"""

import os
import sys
import json
import time
import logging
import shutil
import argparse
from datetime import datetime
from typing import List, Dict, Any, Tuple
from pathlib import Path
from multiprocessing import Pool, Manager, cpu_count
from dotenv import load_dotenv
load_dotenv()

import psycopg2
import psycopg2.extras
import pandas as pd

# Import processors
try:
    from process_netcdf_to_postgres import NetCDFProcessor
    from bgc_ingest import ArgoBGCDataProcessor
except Exception as e:
    print(f"Error importing processors: {e}")
    raise

# Setup logging
LOG = logging.getLogger("bgc_ingest_parallel")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(processName)s - %(levelname)s - %(message)s"
)


class ParallelBGCIngester:
    """Parallel BGC data ingestion with file management"""
    
    def __init__(self, config: Dict[str, Any], db_config: Dict[str, Any], num_workers: int = 10):
        self.config = config
        self.db_config = db_config
        self.num_workers = num_workers
        self.download_dir = Path(config["download_dir"])
        self.ingested_dir = self.download_dir.parent / "ingested_bgc"
        self.log_dir = Path(config["log_dir"])
        
        # Create directories
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.ingested_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup file logging
        log_file = self.log_dir / f"bgc_parallel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        fh = logging.FileHandler(log_file)
        fh.setFormatter(logging.Formatter("%(asctime)s - %(processName)s - %(levelname)s - %(message)s"))
        LOG.addHandler(fh)
        
        LOG.info(f"Initialized parallel ingester with {num_workers} workers")
        LOG.info(f"Download directory: {self.download_dir}")
        LOG.info(f"Ingested directory: {self.ingested_dir}")
    
    def get_files_to_process(self) -> List[str]:
        """Get list of NetCDF files to process"""
        nc_files = list(self.download_dir.glob("*.nc"))
        
        # Filter out already processed files if skip_existing is True
        if self.config.get("skip_existing", True):
            # Check which files are already in ingested folder
            ingested_files = {f.name for f in self.ingested_dir.glob("*.nc")}
            nc_files = [f for f in nc_files if f.name not in ingested_files]
        
        # Limit number of files
        max_files = self.config.get("max_total_files", len(nc_files))
        nc_files = nc_files[:max_files]
        
        LOG.info(f"Found {len(nc_files)} files to process")
        return [str(f) for f in nc_files]
    
    def process_single_file_worker(self, args: Tuple[str, Dict, Dict, Path, Path]) -> Dict[str, Any]:
        """
        Worker function to process a single file
        This runs in a separate process
        """
        filepath, db_config, config, download_dir, ingested_dir = args
        filename = Path(filepath).name
        
        result = {
            'filename': filename,
            'success': False,
            'profiles': 0,
            'measurements': 0,
            'bgc_measurements': 0,
            'error': None
        }
        
        try:
            # Initialize processors (each worker gets its own connection)
            netcdf_processor = NetCDFProcessor(
                data_dir=str(download_dir),
                db_config=db_config
            )
            data_processor = ArgoBGCDataProcessor(db_config)
            
            # Check if already processed in database
            if data_processor.is_file_processed(filename):
                LOG.info(f"[{filename}] Already in database, skipping")
                result['success'] = True
                result['skipped'] = True
                return result
            
            # Process the NetCDF file
            profiles_df, measurements_df = netcdf_processor.process_single_file(filename)
            
            if profiles_df is None or profiles_df.empty:
                LOG.warning(f"[{filename}] No data extracted")
                result['error'] = "No data extracted"
                return result
            
            # Count BGC measurements
            bgc_count = 0
            if 'bgc_parameters' in measurements_df.columns:
                bgc_count = measurements_df['bgc_parameters'].notna().sum()
            
            # Insert into database
            if not profiles_df.empty:
                data_processor.insert_profiles(profiles_df)
            if not measurements_df.empty:
                data_processor.insert_measurements(measurements_df)
            
            # Update result
            result['success'] = True
            result['profiles'] = len(profiles_df)
            result['measurements'] = len(measurements_df)
            result['bgc_measurements'] = bgc_count
            
            # Move file to ingested folder
            try:
                source = Path(filepath)
                destination = ingested_dir / filename
                shutil.move(str(source), str(destination))
                LOG.info(f"[{filename}] Moved to ingested folder")
            except Exception as e:
                LOG.warning(f"[{filename}] Could not move file: {e}")
            
            LOG.info(f"[{filename}] SUCCESS: {len(profiles_df)} profiles, "
                    f"{len(measurements_df)} measurements, {bgc_count} with BGC data")
            
        except Exception as e:
            LOG.error(f"[{filename}] ERROR: {e}")
            result['error'] = str(e)
        
        return result
    
    def run_parallel(self):
        """Run parallel ingestion"""
        start_time = time.time()
        
        # Get files to process
        files = self.get_files_to_process()
        
        if not files:
            LOG.warning("No files to process")
            return {
                'total_files': 0,
                'successful': 0,
                'failed': 0,
                'skipped': 0,
                'total_profiles': 0,
                'total_measurements': 0,
                'total_bgc_measurements': 0,
                'duration': 0
            }
        
        LOG.info(f"Starting parallel processing of {len(files)} files with {self.num_workers} workers")
        
        # Prepare arguments for workers
        worker_args = [
            (filepath, self.db_config, self.config, self.download_dir, self.ingested_dir)
            for filepath in files
        ]
        
        # Use 'spawn' method for macOS compatibility
        import multiprocessing
        ctx = multiprocessing.get_context('spawn')
        
        # Process files in parallel
        results = []
        with ctx.Pool(processes=self.num_workers) as pool:
            # Use imap_unordered for better progress tracking
            for i, result in enumerate(pool.imap_unordered(self.process_single_file_worker, worker_args), 1):
                results.append(result)
                
                # Log progress every 10 files
                if i % 10 == 0:
                    successful = sum(1 for r in results if r['success'])
                    LOG.info(f"Progress: {i}/{len(files)} files processed ({successful} successful)")
        
        # Calculate statistics
        duration = time.time() - start_time
        successful = sum(1 for r in results if r['success'] and not r.get('skipped', False))
        skipped = sum(1 for r in results if r.get('skipped', False))
        failed = sum(1 for r in results if not r['success'])
        total_profiles = sum(r['profiles'] for r in results)
        total_measurements = sum(r['measurements'] for r in results)
        total_bgc = sum(r['bgc_measurements'] for r in results)
        
        stats = {
            'total_files': len(files),
            'successful': successful,
            'failed': failed,
            'skipped': skipped,
            'total_profiles': total_profiles,
            'total_measurements': total_measurements,
            'total_bgc_measurements': total_bgc,
            'duration': duration,
            'files_per_second': len(files) / duration if duration > 0 else 0,
            'errors': [{'file': r['filename'], 'error': r['error']} 
                      for r in results if r['error']]
        }
        
        # Log summary
        LOG.info("=" * 80)
        LOG.info("PARALLEL INGESTION SUMMARY")
        LOG.info("=" * 80)
        LOG.info(f"Total files: {stats['total_files']}")
        LOG.info(f"Successful: {stats['successful']}")
        LOG.info(f"Skipped: {stats['skipped']}")
        LOG.info(f"Failed: {stats['failed']}")
        LOG.info(f"Total profiles: {stats['total_profiles']}")
        LOG.info(f"Total measurements: {stats['total_measurements']}")
        LOG.info(f"BGC measurements: {stats['total_bgc_measurements']}")
        LOG.info(f"Duration: {duration:.2f} seconds")
        LOG.info(f"Speed: {stats['files_per_second']:.2f} files/second")
        
        if stats['errors']:
            LOG.info(f"\nErrors ({len(stats['errors'])}):")
            for err in stats['errors'][:10]:  # Show first 10 errors
                LOG.info(f"  {err['file']}: {err['error']}")
        
        # Save summary to JSON
        summary_file = self.log_dir / f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w') as f:
            json.dump(stats, f, indent=2, default=str)
        LOG.info(f"\nSummary saved to: {summary_file}")
        
        return stats


def load_db_config_from_env():
    """Load database config from environment variables"""
    password = os.getenv("DB_PASSWORD")
    if password is None:
        raise RuntimeError("DB_PASSWORD missing in environment")
    
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", 5432)),
        "user": os.getenv("DB_USERNAME", "postgres"),
        "password": password,
        "database": os.getenv("DB_NAME", "argo_bgc")
    }


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Parallel BGC-Argo data ingestion (optimized for macOS)"
    )
    parser.add_argument(
        "--config", "-c",
        help="Path to JSON config file",
        default=None
    )
    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=10,
        help="Number of worker processes (default: 10)"
    )
    parser.add_argument(
        "--max-files", "-m",
        type=int,
        default=None,
        help="Maximum number of files to process"
    )
    args = parser.parse_args()
    
    # Default configuration
    config = {
        "download_dir": "./data/bgc_downloads/",
        "log_dir": "./logs/",
        "max_total_files": args.max_files if args.max_files else 1000000,
        "skip_existing": True
    }
    
    # Load user config if provided
    if args.config and os.path.exists(args.config):
        with open(args.config, 'r') as f:
            user_config = json.load(f)
            config.update(user_config)
    
    # Override max_files if specified
    if args.max_files:
        config["max_total_files"] = args.max_files
    
    # Load database config
    try:
        db_config = load_db_config_from_env()
    except Exception as e:
        LOG.error(f"Database config error: {e}")
        sys.exit(1)
    
    LOG.info(f"Using database: {db_config['database']}")
    LOG.info(f"Workers: {args.workers}")
    LOG.info(f"Max files: {config['max_total_files']}")
    
    # Create ingester and run
    ingester = ParallelBGCIngester(config, db_config, num_workers=args.workers)
    stats = ingester.run_parallel()
    
    # Print summary to console
    print("\n" + "=" * 80)
    print("PARALLEL BGC INGESTION COMPLETED")
    print("=" * 80)
    print(f"Files processed: {stats['successful']}/{stats['total_files']}")
    print(f"Profiles: {stats['total_profiles']}")
    print(f"Measurements: {stats['total_measurements']}")
    print(f"BGC measurements: {stats['total_bgc_measurements']}")
    print(f"Duration: {stats['duration']:.2f} seconds")
    print(f"Speed: {stats['files_per_second']:.2f} files/second")
    
    if stats['failed'] > 0:
        print(f"\n⚠️  {stats['failed']} files failed (see logs for details)")
    
    print("\n✅ Ingested files moved to: data/ingested_bgc/")
    print("=" * 80)


if __name__ == "__main__":
    # Required for macOS multiprocessing
    import multiprocessing
    multiprocessing.set_start_method('spawn', force=True)
    main()
