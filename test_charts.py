import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import create_engine

# Database connection
engine = create_engine("postgresql://postgres:parv12345@localhost:5432/testing_2025")

def fetch_argo_data(float_id='5906527', limit_profiles=5):
    """
    Fetch Argo float data from the database for multiple profiles of a float.
    
    Args:
        float_id (str): The float ID to fetch data for
        limit_profiles (int): Maximum number of profiles to fetch
        
    Returns:
        dict: Dictionary of DataFrames keyed by profile_id
    """
    import psycopg2
    from psycopg2 import sql
    
    conn = psycopg2.connect(
        dbname="testing_2025",
        user="postgres",
        password="parv12345",
        host="localhost",
        port="5432"
    )
    
    # First, get the most recent N profiles for the float with their locations
    profile_query = """
    SELECT DISTINCT ON (p.global_profile_id)
        p.global_profile_id, 
        p.cycle_number, 
        m.datetime,
        m.latitude,
        m.longitude
    FROM argo_profiles p
    JOIN argo_measurements m ON m.global_profile_id = p.global_profile_id
    WHERE p.float_id = %s
    ORDER BY p.global_profile_id, m.datetime DESC
    LIMIT %s;
    """
    
    print(f"Fetching profile list for float {float_id}...")
    profiles_df = pd.read_sql_query(profile_query, conn, params=(float_id, limit_profiles))
    
    # Print the list of profiles with their dates, cycle numbers, and locations
    print("\nAvailable profiles:")
    for _, row in profiles_df.iterrows():
        profile_time = row['datetime'].strftime("%Y-%m-%d %H:%M")
        print(f"Cycle: {row['cycle_number']}, Date: {profile_time}")
        print(f"  Profile ID: {row['global_profile_id']}")
        print(f"  Location: Lat {row['latitude']:.4f}°, Lon {row['longitude']:.4f}°")
    print()
    
    if profiles_df.empty:
        print(f"No profiles found for float {float_id}")
        conn.close()
        return {}
    
    # Get data for all selected profiles
    profile_ids = tuple(profiles_df['global_profile_id'])
    query = """
    SELECT
        p.float_id,
        p.global_profile_id,
        p.cycle_number,
        m.datetime,
        m.level,
        m.pressure_adjusted as pressure,
        m.temperature_adjusted as temperature,
        m.salinity_adjusted as salinity,
        m.latitude,
        m.longitude
    FROM argo_profiles p
    JOIN argo_measurements m
        ON m.global_profile_id = p.global_profile_id
    WHERE p.global_profile_id IN %s
    ORDER BY p.cycle_number, m.level
    """
    
    print(f"Fetching data for {len(profile_ids)} profiles...")
    df = pd.read_sql_query(query, conn, params=(profile_ids,))
    conn.close()
    
    # Group by profile_id and include cycle number in the label
    profiles = {}
    for (profile_id, cycle_num), group in df.groupby(['global_profile_id', 'cycle_number']):
        profile_time = group['datetime'].iloc[0].strftime("%Y-%m-%d %H:%M")
        print(f"Cycle {cycle_num} (ID: {profile_id}, {profile_time}): {len(group)} measurements")
        # Use cycle number as the key for better readability
        profiles[f"Cycle {cycle_num}"] = group
    
    return profiles

def plot_argo_depth_profiles(profiles_dict):
    """Plot multiple Argo float profiles with depth-based coloring in 2D."""
    if not profiles_dict:
        print("No data to plot!")
        return
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(12, 8))

    # Create a colormap for different profiles
    profile_colors = plt.cm.tab10(np.linspace(0, 1, len(profiles_dict)))
    
    # Initialize legend handles and labels
    legend_handles = []
    legend_labels = []
    
    # Find min/max values for consistent axis scaling
    all_salinity = []
    all_temperature = []
    all_pressure = []
    
    for df in profiles_dict.values():
        if not df.empty:
            all_salinity.extend(df['salinity'].dropna().values)
            all_temperature.extend(df['temperature'].dropna().values)
            all_pressure.extend(df['pressure'].dropna().values)
    
    # Set axis limits with some padding
    sal_min, sal_max = (min(all_salinity), max(all_salinity)) if all_salinity else (0, 40)
    temp_min, temp_max = (min(all_temperature), max(all_temperature)) if all_temperature else (0, 30)
    
    # Add some padding to the axis limits
    sal_pad = (sal_max - sal_min) * 0.1
    temp_pad = (temp_max - temp_min) * 0.1
    
    # Create a colormap for depth
    depth_cmap = plt.cm.viridis
    
    for idx, (profile_id, df) in enumerate(profiles_dict.items()):
        if df.empty:
            continue
            
        # Convert datetime if needed
        if 'datetime' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['datetime']):
            df['datetime'] = pd.to_datetime(df['datetime'])
        
        # Sort by pressure (depth)
        df = df.sort_values('pressure')
        
        # Get profile metadata for legend
        profile_time = df['datetime'].iloc[0].strftime("%Y-%m-%d %H:%M") if 'datetime' in df.columns else 'N/A'
        lat = df['latitude'].iloc[0] if 'latitude' in df.columns else None
        lon = df['longitude'].iloc[0] if 'longitude' in df.columns else None
        
        # Get this profile's color
        profile_color = profile_colors[idx % len(profile_colors)]
        
        # Create scatter plot with depth-based coloring
        scatter = ax.scatter(
            df['salinity'],  # x-axis
            df['temperature'],  # y-axis
            c=df['pressure'],  # Color by depth
            cmap=depth_cmap,
            s=40,
            alpha=0.7,
            edgecolors=profile_color,  # Use profile color for edges
            linewidths=0.5,
            label=f"Profile {profile_id}"
        )
        
        # Add line connecting the points for better visualization
        line, = ax.plot(
            df['salinity'],
            df['temperature'],
            color=profile_color,  # Use profile color for the line
            linewidth=1.0,
            alpha=0.6
        )
        
        # Create legend entry with lat/lon if available
        label = f"Profile {profile_id} - {profile_time}"
        if lat is not None and lon is not None:
            label += f"\n({lat:.2f}°N, {lon:.2f}°E)"
        
        # Add a marker to the legend with the profile's color
        legend_handles.append(plt.Line2D([0], [0], 
                                       marker='o', 
                                       color='w',
                                       markerfacecolor=profile_color,
                                       markersize=10, 
                                       alpha=0.8,
                                       markeredgecolor='k',
                                       markeredgewidth=0.5))
        legend_labels.append(label)
    
    # Set axis labels and title
    ax.set_xlabel('Salinity (PSU)', fontsize=12)
    ax.set_ylabel('Temperature (°C)', fontsize=12)
    
    # Set axis limits with padding
    ax.set_xlim(sal_min - sal_pad, sal_max + sal_pad)
    ax.set_ylim(temp_min - temp_pad, temp_max + temp_pad)
    
    # Add colorbar for depth
    cbar = plt.colorbar(scatter, ax=ax, pad=0.02)
    cbar.set_label('Depth (dbar)', fontsize=12)
    
    # Add grid
    ax.grid(True, linestyle='--', alpha=0.4)
    
    # Add main title
    if profiles_dict:
        first_df = next(iter(profiles_dict.values()))
        float_id = first_df['float_id'].iloc[0] if 'float_id' in first_df.columns else 'N/A'
        ax.set_title(f'Argo Float {float_id} - T-S Diagram with Depth Coloring', 
                   fontsize=14, pad=20)
    
    # Add legend
    legend = ax.legend(legend_handles, legend_labels, 
                      loc='upper right', 
                      bbox_to_anchor=(1.4, 1.0),
                      fancybox=True, 
                      shadow=True,
                      fontsize=9)
    
    # Make legend background more transparent
    legend.get_frame().set_alpha(0.9)
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Visualize Argo float data')
    parser.add_argument('--float_id', type=str, default='5906527',
                       help='Float ID to visualize (default: 5906527)')
    parser.add_argument('--profiles', type=int, default=5,
                       help='Maximum number of profiles to visualize (default: 5)')
    
    args = parser.parse_args()
    
    print(f"Starting Argo Data Visualization for float {args.float_id}...")
    profiles = fetch_argo_data(float_id=args.float_id, limit_profiles=args.profiles)
    
    if profiles:
        print(f"\nFound {len(profiles)} profiles")
        plot_argo_depth_profiles(profiles)
    else:
        print("\nNo profile data found")