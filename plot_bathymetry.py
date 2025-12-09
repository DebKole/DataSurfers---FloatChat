#!/usr/bin/env python3
"""
UPDATED:
1. Heatmap of Argo-derived depths (0–2000+ m)
2. Heatmap of flagged deltas (argo_depth <=2000 AND delta > 5 m)
3. Plot pins at flagged positions with delta label
"""

import os
import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from dotenv import load_dotenv
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.colors import LogNorm, Normalize

load_dotenv()

class ArgoDensityMapper:
    def __init__(self, db_config, output_dir="./density_maps"):
        self.db_config = db_config
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def get_db_connection(self, db_name):
        config = self.db_config.copy()
        config['database'] = db_name
        return psycopg2.connect(**config)

    def fetch_measurements_with_depth(self, db_name):
        """
        Fetch latitude, longitude, argo_depth, true_depth from DB.
        NOTE: Requires columns:
            - pressure (max depth reached by Argo)
            - bathy_depth (from GEBCO)
        """
        try:
            conn = self.get_db_connection(db_name)

            # UPDATED: Use 'pressure_adjusted' instead of 'pressure'
            # UPDATED: Removed 'bathy_depth' as it does not exist in the current schema
            query = """
                SELECT 
                    latitude, longitude,
                    pressure_adjusted AS argo_depth
                FROM argo_measurements
                WHERE latitude IS NOT NULL 
                  AND longitude IS NOT NULL
                  AND pressure_adjusted IS NOT NULL;
            """
            df = pd.read_sql(query, conn)
            conn.close()

            print(f"  ✓ Loaded {len(df):,} rows from {db_name}")

            # Compute delta if true_depth is available (it's currently not)
            if "true_depth" in df.columns:
                df["delta"] = (df["argo_depth"] - df["true_depth"]).abs()
                # Flag condition
                df["flag"] = (df["argo_depth"] <= 2000) & (df["delta"] > 5)
            else:
                # print("  ! 'true_depth' (bathy_depth) not in DB. Skipping delta check.")
                df["delta"] = np.nan
                df["flag"] = False

            return df

        except Exception as e:
            print(f"  ✗ Error fetching data from {db_name}: {e}")
            return pd.DataFrame()

    # -------------------------------------------------------------------------
    # NEW: HEATMAP OF ARGO DEPTHS (0–2000+ m)
    # -------------------------------------------------------------------------
    def plot_argo_depth_heatmap(self, df, year, region):
        print(f"  Plotting Argo-derived depth heatmap for {year}...")

        fig = plt.figure(figsize=(20, 12))
        ax = plt.axes(projection=ccrs.PlateCarree())

        ax.add_feature(cfeature.LAND, facecolor='lightgray')
        ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
        ax.gridlines(draw_labels=True)

        # Depth heatmap (non-log)
        hb = ax.hexbin(
            df["longitude"],
            df["latitude"],
            C=df["argo_depth"],
            gridsize=80,
            reduce_C_function=np.mean,
            cmap="viridis",
            vmin=0,
            vmax=2200,
            transform=ccrs.PlateCarree()
        )

        cbar = plt.colorbar(hb, ax=ax, pad=0.02, shrink=0.7)
        cbar.set_label("Argo-Derived Depth (m)", fontsize=14)

        ax.set_title(
            f"Argo-Derived Ocean Depth Heatmap - {year}\nRange: 0–>2000 m",
            fontsize=18,
            pad=20
        )

        filepath = os.path.join(self.output_dir, f"{region}_{year}_argo_depths.png")
        plt.savefig(filepath, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"  ✓ Saved depth heatmap: {filepath}")

    # -------------------------------------------------------------------------
    # NEW: HEATMAP OF FLAGGED DELTAS + PIN LOCATIONS
    # -------------------------------------------------------------------------
    def plot_flagged_delta_map(self, df, year, region):
        print(f"  Plotting flagged-delta heatmap for {year}...")

        flagged = df[df["flag"] == True]
        if flagged.empty:
            print("  No flagged delta points for this year.")
            return

        fig = plt.figure(figsize=(20, 12))
        ax = plt.axes(projection=ccrs.PlateCarree())

        ax.add_feature(cfeature.LAND, facecolor='lightgray')
        ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
        ax.gridlines(draw_labels=True)

        # Heatmap of flagged deltas
        hb = ax.hexbin(
            flagged["longitude"],
            flagged["latitude"],
            C=flagged["delta"],
            gridsize=80,
            reduce_C_function=np.mean,
            cmap="Reds",
            vmin=5,
            vmax=flagged["delta"].max(),
            transform=ccrs.PlateCarree()
        )

        cbar = plt.colorbar(hb, ax=ax, pad=0.02, shrink=0.7)
        cbar.set_label("Delta (m): |Argo − Bathymetry|", fontsize=14)

        # Drop pin markers
        ax.scatter(
            flagged["longitude"], flagged["latitude"],
            color="black", s=10, transform=ccrs.PlateCarree()
        )

        # Label with Δ values
        for _, row in flagged.iterrows():
            ax.text(
                row["longitude"], row["latitude"],
                f"{row['delta']:.1f}",
                fontsize=6, color="black",
                transform=ccrs.PlateCarree()
            )

        ax.set_title(
            f"Flagged Bathymetry Errors - {year}\n(Argo depth ≤ 2000 m and Δ > 5 m)",
            fontsize=18,
            pad=20
        )

        filepath = os.path.join(self.output_dir, f"{region}_{year}_flagged_deltas.png")
        plt.savefig(filepath, dpi=300, bbox_inches="tight")
        plt.close()

        print(f"  ✓ Saved flagged-delta map: {filepath}")

    # -------------------------------------------------------------------------
    # MAIN YEAR PROCESSOR
    # -------------------------------------------------------------------------
    def process_all_years(self, years=None, region="indian_ocean"):
        if years is None:
            years = range(2015, 2026)

        print(f"Processing Argo Bathymetry Maps for region = {region}")
        print("=" * 60)

        for year in years:
            suffix = str(year)[-2:]
            db_name = f"argo_{region}_{suffix}"

            print(f"\nProcessing {year} (db = {db_name})...")
            df = self.fetch_measurements_with_depth(db_name)

            if df.empty:
                print("  Skipping year due to empty DB")
                continue

            # 1️⃣ Heatmap of Argo depths
            self.plot_argo_depth_heatmap(df, year, region)

            # 2️⃣ Heatmap + pins for flagged deltas
            self.plot_flagged_delta_map(df, year, region)

        print("\nComplete!")

# -------------------------------------------------------------------------
# CONFIG AND ENTRY
# -------------------------------------------------------------------------
def load_db_config():
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", 5432)),
        "user": os.getenv("DB_USERNAME", "postgres"),
        "password": os.getenv("DB_PASSWORD"),
        "database": "postgres"
    }

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate Argo depth and delta maps")
    parser.add_argument("--region", "-r", default="indian_ocean")
    parser.add_argument("--output", "-o", default="./density_maps")
    parser.add_argument("--years", "-y", nargs="+", type=int)
    args = parser.parse_args()

    db_config = load_db_config()
    if not db_config["password"]:
        print("DB_PASSWORD missing")
        return

    mapper = ArgoDensityMapper(db_config, output_dir=args.output)
    mapper.process_all_years(years=args.years, region=args.region)

if __name__ == "__main__":
    main()