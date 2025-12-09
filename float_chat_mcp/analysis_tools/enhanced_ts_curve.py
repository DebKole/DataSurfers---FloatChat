import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import psycopg2
from typing import Dict

# --------------------------
# Database Connection
# --------------------------

def get_db_connection():
    return psycopg2.connect(
        dbname="january_data",
        user="postgres",
        password="parv12345",
        host="localhost",
        port="5432"
    )

# --------------------------
# Fetch Argo Data
# --------------------------

def fetch_argo_data(float_id: str, limit_profiles: int = 5) -> Dict[str, pd.DataFrame]:
    """
    Fetch Argo float profiles & measurement data.
    """
    conn = None
    try:
        conn = get_db_connection()

        # Step 1 — get latest cycles for this float
        profile_query = """
        SELECT DISTINCT ON (p.global_profile_id)
            p.global_profile_id,
            p.cycle_number,
            m.datetime,
            m.latitude,
            m.longitude
        FROM argo_profiles p
        JOIN argo_measurements m
            ON m.global_profile_id = p.global_profile_id
        WHERE p.float_id = %s
        ORDER BY p.global_profile_id, m.datetime DESC
        LIMIT %s;
        """

        profiles_df = pd.read_sql_query(
            profile_query, conn, params=(float_id, limit_profiles)
        )

        if profiles_df.empty:
            print("No profiles found.")
            return {}

        profile_ids = profiles_df["global_profile_id"].tolist()

    except Exception as e:
        print(f"Error loading profiles: {e}")
        return {}

    finally:
        if conn:
            conn.close()

    # Step 2 — fetch measurements with correct column names
    try:
        conn = get_db_connection()

        query = """
        SELECT
            p.float_id,
            p.global_profile_id,
            p.cycle_number,
            m.datetime,
            m.level,
            m.pressure,
            m.temperature,
            m.salinity,
            m.latitude,
            m.longitude
        FROM argo_profiles p
        JOIN argo_measurements m
            ON m.global_profile_id = p.global_profile_id
        WHERE p.global_profile_id = ANY(%s)
        ORDER BY p.cycle_number, m.level;
        """

        df = pd.read_sql_query(query, conn, params=(profile_ids,))

    except Exception as e:
        print(f"Error fetching measurement data: {e}")
        return {}

    finally:
        if conn:
            conn.close()

    if df.empty:
        print("No measurement rows found.")
        return {}

    # Grouping by cycle
    profiles = {}
    for (profile_id, cycle), group_df in df.groupby(["global_profile_id", "cycle_number"]):
        label = f"Cycle {int(cycle)}"
        profiles[label] = group_df

    return profiles

# --------------------------
# Plot T-S Diagram
# --------------------------

def plot_argo_depth_profiles(profiles_dict):
    """Plot temperature-salinity diagram with pressure coloring."""
    if not profiles_dict:
        print("No data to plot.")
        return

    fig, ax = plt.subplots(figsize=(12, 8))

    profile_colors = plt.cm.tab10(np.linspace(0, 1, len(profiles_dict)))

    all_sal, all_temp = [], []

    for df in profiles_dict.values():
        all_sal.extend(df["salinity"].dropna().tolist())
        all_temp.extend(df["temperature"].dropna().tolist())

    if not all_sal or not all_temp:
        print("Missing temperature/salinity in data.")
        return

    sal_min, sal_max = min(all_sal), max(all_sal)
    temp_min, temp_max = min(all_temp), max(all_temp)

    sal_pad = (sal_max - sal_min) * 0.1
    temp_pad = (temp_max - temp_min) * 0.1

    scatter_obj = None
    legend_handles, legend_labels = [], []

    for idx, (profile_label, df) in enumerate(profiles_dict.items()):
        df_sorted = df.sort_values("pressure")
        color = profile_colors[idx]

        scatter_obj = ax.scatter(
            df_sorted["salinity"],
            df_sorted["temperature"],
            c=df_sorted["pressure"],
            cmap="viridis",
            s=40,
            alpha=0.75,
            edgecolors=color,
            linewidths=0.5
        )

        ax.plot(
            df_sorted["salinity"],
            df_sorted["temperature"],
            color=color,
            linewidth=1.2
        )

        handle = plt.Line2D(
            [0], [0], marker="o", color="w",
            markerfacecolor=color, markeredgecolor="k",
            markersize=10
        )

        legend_handles.append(handle)
        legend_labels.append(profile_label)

    ax.set_title("Enhanced Temperature-Salinity Diagram", fontsize=15)
    ax.set_xlabel("Salinity (PSU)", fontsize=13)
    ax.set_ylabel("Temperature (°C)", fontsize=13)

    ax.set_xlim(sal_min - sal_pad, sal_max + sal_pad)
    ax.set_ylim(temp_min - temp_pad, temp_max + temp_pad)

    if scatter_obj:
        cbar = plt.colorbar(scatter_obj, ax=ax, pad=0.02)
        cbar.set_label("Pressure (dbar)")

    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend(legend_handles, legend_labels, loc="upper right")

    plt.tight_layout()
    plt.show()

# --------------------------
# API Function
# --------------------------

def get_enhanced_ts_curve(float_id: str, limit: int = 5) -> Dict[str, str]:
    """
    Main function to generate an enhanced T-S diagram for a given float.
    
    Args:
        float_id: The Argo float ID to generate the diagram for
        limit: Maximum number of profiles to include
        
    Returns:
        Dictionary with 'image' (base64-encoded PNG) or 'error' message
    """
    import io
    import base64
    
    if not float_id or not isinstance(float_id, str):
        return {"error": "Invalid float ID provided"}
        
    try:
        print(f"Generating T-S diagram for float {float_id}")
        profiles = fetch_argo_data(float_id, limit)

        if not profiles:
            error_msg = f"No valid profile data found for float {float_id}"
            print(error_msg)
            return {"error": error_msg}

        print(f"Generating plot for {len(profiles)} profiles")
        
        # Create the plot
        fig, ax = plt.subplots(figsize=(12, 8))
        profile_colors = plt.cm.tab10(np.linspace(0, 1, len(profiles)))
        all_sal, all_temp = [], []

        # First pass: collect all data for scaling
        for df in profiles.values():
            all_sal.extend(df["salinity"].dropna().tolist())
            all_temp.extend(df["temperature"].dropna().tolist())

        if not all_sal or not all_temp:
            error_msg = "No valid temperature/salinity data found"
            print(error_msg)
            return {"error": error_msg}

        sal_min, sal_max = min(all_sal), max(all_sal)
        temp_min, temp_max = min(all_temp), max(all_temp)
        sal_pad = (sal_max - sal_min) * 0.1
        temp_pad = (temp_max - temp_min) * 0.1

        scatter_obj = None
        legend_handles, legend_labels = [], []

        # Second pass: plot the data
        for idx, (profile_label, df) in enumerate(profiles.items()):
            df_sorted = df.sort_values("pressure")
            color = profile_colors[idx]

            scatter_obj = ax.scatter(
                df_sorted["salinity"],
                df_sorted["temperature"],
                c=df_sorted["pressure"],
                cmap="viridis",
                s=40,
                alpha=0.75,
                edgecolors=color,
                linewidths=0.5
            )

            ax.plot(
                df_sorted["salinity"],
                df_sorted["temperature"],
                color=color,
                linewidth=1.2
            )

            handle = plt.Line2D(
                [0], [0], marker="o", color="w",
                markerfacecolor=color, markeredgecolor="k",
                markersize=10
            )

            legend_handles.append(handle)
            legend_labels.append(profile_label)

        # Finalize the plot
        ax.set_title("Enhanced Temperature-Salinity Diagram", fontsize=15)
        ax.set_xlabel("Salinity (PSU)", fontsize=13)
        ax.set_ylabel("Temperature (°C)", fontsize=13)
        ax.set_xlim(sal_min - sal_pad, sal_max + sal_pad)
        ax.set_ylim(temp_min - temp_pad, temp_max + temp_pad)

        if scatter_obj:
            cbar = plt.colorbar(scatter_obj, ax=ax, pad=0.02)
            cbar.set_label("Pressure (dbar)")

        ax.grid(True, linestyle="--", alpha=0.4)
        ax.legend(legend_handles, legend_labels, loc="upper right")
        plt.tight_layout()

        # Save to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        plt.close(fig)
        
        return {
            "image": base64.b64encode(buf.getvalue()).decode("utf-8"),
            "profiles_processed": len(profiles),
            "status": "success"
        }
        
    except Exception as e:
        error_msg = f"Error generating T-S diagram: {str(e)}"
        print(error_msg)
        return {"error": error_msg}
    finally:
        plt.close('all')

# --------------------------
# Main Program
# --------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--float_id", type=str, default="5906527")
    parser.add_argument("--profiles", type=int, default=5)
    args = parser.parse_args()

    print(f"Loading float {args.float_id} ...")

    profiles = fetch_argo_data(args.float_id, args.profiles)

    if profiles:
        print(f"Loaded {len(profiles)} profiles.")
        plot_argo_depth_profiles(profiles)
    else:
        print("No data returned.")
