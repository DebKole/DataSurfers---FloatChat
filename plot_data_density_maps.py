#!/usr/bin/env python3
"""
Plot data point density maps from Argo databases based on lat-long coordinates.
Creates separate maps for each year (2015-2025) and saves them as PNG images.
"""

import os
import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from dotenv import load_dotenv
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.colors import LogNorm

load_dotenv()


class ArgoDensityMapper:
    def __init__(self, db_config, output_dir="./density_maps"):
        """
        Initialize the density mapper.
        
        Args:
            db_config: Database configuration dict
            output_dir: Directory to save PNG images
        """
        self.db_config = db_config
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
    def get_db_connection(self, db_name):
        """Create database connection with specific database name."""
        config = self.db_config.copy()
        config['database'] = db_name
        return psycopg2.connect(**config)
    
    def fetch_measurement_locations(self, db_name):
        """Fetch all measurement locations from a database."""
        try:
            conn = self.get_db_connection(db_name)
            
            # First get count for progress
            count_query = """
                SELECT COUNT(*) as total
                FROM argo_measurements 
                WHERE latitude IS NOT NULL 
                AND longitude IS NOT NULL
            """
            cursor = conn.cursor()
            cursor.execute(count_query)
            total = cursor.fetchone()[0]
            cursor.close()
            
            print(f"  Fetching {total:,} measurements from {db_name}...")
            
            # Fetch data using the spatial index
            query = """
                SELECT latitude, longitude 
                FROM argo_measurements 
                WHERE latitude IS NOT NULL 
                AND longitude IS NOT NULL
            """
            df = pd.read_sql(query, conn)
            conn.close()
            
            print(f"  ✓ Loaded {len(df):,} measurements")
            return df
        except Exception as e:
            print(f"  ✗ Error fetching data from {db_name}: {e}")
            return pd.DataFrame()
    
    def plot_density_map(self, df, year, region="indian_ocean"):
        """
        Create a density map using hexbin plot.
        
        Args:
            df: DataFrame with latitude and longitude columns
            year: Year for the title
            region: Ocean region name
        """
        if df.empty:
            print(f"  No data to plot for {year}")
            return None
        
        # Print data extent for debugging
        print(f"  Data extent: Lat [{df['latitude'].min():.2f}, {df['latitude'].max():.2f}], "
              f"Lon [{df['longitude'].min():.2f}, {df['longitude'].max():.2f}]")
        
        # Create figure with cartopy projection
        fig = plt.figure(figsize=(20, 12))
        ax = plt.axes(projection=ccrs.PlateCarree())
        
        # Add map features
        ax.add_feature(cfeature.LAND, facecolor='lightgray', edgecolor='black', linewidth=0.5)
        ax.add_feature(cfeature.OCEAN, facecolor='#E8F4F8')
        ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
        ax.gridlines(draw_labels=True, linewidth=0.5, alpha=0.5, linestyle='--')
        
        # Create hexbin density plot
        hexbin = ax.hexbin(
            df['longitude'], 
            df['latitude'],
            gridsize=80,
            cmap='hot_r',
            mincnt=1,
            norm=LogNorm(),
            transform=ccrs.PlateCarree(),
            alpha=0.8,
            edgecolors='none'
        )
        
        # Add colorbar
        cbar = plt.colorbar(hexbin, ax=ax, orientation='vertical', pad=0.02, shrink=0.7)
        cbar.set_label('Number of Measurements (log scale)', fontsize=14, fontweight='bold')
        
        # Set title
        region_title = region.replace('_', ' ').title()
        ax.set_title(f'Argo Measurement Data Point Density - {region_title} - {year}\n'
                     f'Total Measurements: {len(df):,}', 
                     fontsize=18, fontweight='bold', pad=20)
        
        # Use global extent to show all ocean data
        ax.set_global()
        
        plt.tight_layout()
        
        # Save figure
        filename = f"{region}_{year}_density.png"
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  Saved map: {filepath}")
        return filepath
    
    def process_all_years(self, years=None, region="indian_ocean"):
        """
        Process all years and create density maps.
        
        Args:
            years: List of years to process (default: 2015-2025)
            region: Ocean region name
        """
        if years is None:
            years = range(2015, 2026)  # 2015-2025
        
        print(f"Processing density maps for {region}...")
        print(f"Output directory: {self.output_dir}")
        print("=" * 60)
        
        for year in years:
            year_suffix = str(year)[-2:]  # Get last 2 digits (e.g., "15" for 2015)
            db_name = f"argo_{region}_{year_suffix}"
            
            print(f"\nProcessing {year} (database: {db_name})...")
            
            # Fetch data from argo_measurements table
            df = self.fetch_measurement_locations(db_name)
            
            if not df.empty:
                # Create map
                self.plot_density_map(df, year, region)
            else:
                print(f"  Skipping {year} - no data available")
        
        print("\n" + "=" * 60)
        print(f"Completed! All maps saved to: {self.output_dir}")


def load_db_config():
    """Load database configuration from environment variables."""
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", 5432)),
        "user": os.getenv("DB_USERNAME", "postgres"),
        "password": os.getenv("DB_PASSWORD"),
        "database": "postgres"  # Default, will be overridden per query
    }


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate Argo data density maps")
    parser.add_argument("--region", "-r", default="indian_ocean", 
                        help="Ocean region (indian_ocean, atlantic_ocean, pacific_ocean)")
    parser.add_argument("--output", "-o", default="./density_maps",
                        help="Output directory for PNG files")
    parser.add_argument("--years", "-y", nargs="+", type=int,
                        help="Specific years to process (default: 2015-2025)")
    args = parser.parse_args()
    
    # Load database config
    db_config = load_db_config()
    
    if not db_config["password"]:
        print("Error: DB_PASSWORD not set in environment")
        return
    
    # Create mapper and process
    mapper = ArgoDensityMapper(db_config, output_dir=args.output)
    mapper.process_all_years(years=args.years, region=args.region)


if __name__ == "__main__":
    main()
