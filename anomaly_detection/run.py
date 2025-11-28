#!/usr/bin/env python3
"""
Simple launcher for Argo Anomaly Detection Pipeline
Usage: python run.py
"""

import sys
import os
from pathlib import Path

def print_header():
    print("=" * 80)
    print("ARGO ANOMALY DETECTION PIPELINE")
    print("=" * 80)
    print()

def print_menu():
    print("SELECT MODE:")
    print("-" * 80)
    print("1) Quick Test (5 min)")
    print("   - Test with 1 week of data")
    print("   - Verify setup and configuration")
    print()
    print("2) Full Pipeline (30-60 min)")
    print("   - Complete training and detection")
    print("   - Process all your data")
    print("   - Generate final results")
    print()
    print("3) API Server")
    print("   - Start REST API for real-time detection")
    print("   - Access at http://localhost:8000/docs")
    print()
    print("4) Jupyter Notebook")
    print("   - Interactive exploration")
    print("   - Visualization and analysis")
    print()
    print("0) Exit")
    print("-" * 80)

def check_setup():
    """Check if basic setup is complete."""
    issues = []
    
    # Check config file
    if not Path('config/config.yaml').exists():
        issues.append("❌ config/config.yaml not found")
    
    # Check data directory
    try:
        import yaml
        with open('config/config.yaml') as f:
            config = yaml.safe_load(f)
        data_path = config['database']['parquet_path']
        if not Path(data_path).exists():
            issues.append(f"⚠️  Data directory not found: {data_path}")
    except Exception as e:
        issues.append(f"⚠️  Could not read config: {e}")
    
    # Check dependencies
    try:
        import pandas
        import numpy
        import sklearn
        import lightgbm
    except ImportError as e:
        issues.append(f"⚠️  Missing dependency: {e.name}")
    
    if issues:
        print("⚠️  Setup Issues:")
        for issue in issues:
            print(f"   {issue}")
        print()
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    else:
        print("✅ Setup verified")
        print()

def run_quick_test():
    """Run quick test."""
    print("\n🚀 Running Quick Test...")
    print("=" * 80)
    os.system('python pipeline/quick_test.py')

def run_full_pipeline():
    """Run full pipeline."""
    print("\n🚀 Running Full Pipeline...")
    print("=" * 80)
    print()
    
    # Get date range
    start_date = input("Start date (YYYY-MM-DD, default: 2022-01-01): ").strip()
    if not start_date:
        start_date = "2022-01-01"
    
    end_date = input("End date (YYYY-MM-DD, default: 2024-12-31): ").strip()
    if not end_date:
        end_date = "2024-12-31"
    
    print(f"\nProcessing data from {start_date} to {end_date}")
    print()
    
    # Update config
    try:
        import yaml
        with open('config/config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        config['data']['start_date'] = start_date
        config['data']['end_date'] = end_date
        with open('config/config.yaml', 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
    except Exception as e:
        print(f"⚠️  Could not update config: {e}")
    
    # Run pipeline
    os.system('python pipeline/train_and_detect.py')
    
    print("\n" + "=" * 80)
    print("✅ PIPELINE COMPLETE!")
    print("=" * 80)
    print("\nResults saved to:")
    print("  - artifacts/results/anomaly_scores.csv")
    print("  - artifacts/results/anomalous_profiles.csv")
    print("  - artifacts/polygons/regions.geojson")
    print("  - artifacts/models/")
    print("\nNext steps:")
    print("  1. View results: cat artifacts/results/anomaly_scores.csv")
    print("  2. Start API: python run.py (choose option 3)")
    print("  3. Visualize: python run.py (choose option 4)")

def run_api_server():
    """Start API server."""
    print("\n🚀 Starting API Server...")
    print("=" * 80)
    print("\nAPI will be available at:")
    print("  - Docs: http://localhost:8000/docs")
    print("  - Health: http://localhost:8000/health")
    print("\nPress Ctrl+C to stop")
    print()
    os.system('python api/app.py')

def run_jupyter():
    """Start Jupyter notebook."""
    print("\n🚀 Starting Jupyter Notebook...")
    print("=" * 80)
    print("\nJupyter will open in your browser")
    print("Navigate to: notebooks/01_quick_start.ipynb")
    print("\nPress Ctrl+C to stop")
    print()
    os.system('jupyter notebook notebooks/')

def main():
    """Main entry point."""
    print_header()
    
    # Check setup
    print("🔍 Checking setup...")
    check_setup()
    
    while True:
        print_menu()
        choice = input("Enter choice (0-4): ").strip()
        
        if choice == '1':
            run_quick_test()
            break
        elif choice == '2':
            run_full_pipeline()
            break
        elif choice == '3':
            run_api_server()
            break
        elif choice == '4':
            run_jupyter()
            break
        elif choice == '0':
            print("\nExiting...")
            sys.exit(0)
        else:
            print("\n❌ Invalid choice. Please try again.\n")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
