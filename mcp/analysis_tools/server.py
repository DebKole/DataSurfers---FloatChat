from fastmcp import FastMCP
import pandas as pd
import numpy as np
from typing import Dict, List, Any,Optional
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Create the MCP server instance
mcp = FastMCP("analysis_tools")

# Import all tools after mcp instance is created to avoid circular imports
# The @mcp.tool decorators will register them automatically


@mcp.tool
def argo_temp_trend(data: List[Dict[str, Any]], show_plot: bool = False, window: int = 20) -> Dict[str, List]:
    """
    Analyze temperature trends from ARGO data.
    
    Args:
        data: List of dictionaries with 'datetime' and 'temperature' keys
        show_plot: Whether to display a plot (default: False)
        window: Rolling window size for smoothing (default: 20)
    
    Returns:
        Dictionary with profiles containing measurements (datetime and temperature)
    """
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    if 'datetime' not in df.columns or 'temperature' not in df.columns:
        raise ValueError("Required columns: 'datetime', 'temperature'")

    # Create time-series with datetime index
    df_clean = df[['datetime', 'temperature']].dropna().copy()
    df_clean['datetime'] = pd.to_datetime(df_clean['datetime'])
    df_clean = df_clean.sort_values('datetime').set_index('datetime')
    
    # Calculate rolling average for smoothing
    df_clean['temp_smooth'] = df_clean['temperature'].rolling(window=window, center=True, min_periods=1).mean()
    df_clean = df_clean.reset_index()
    
    # Create measurements list
    measurements = []
    for _, row in df_clean.iterrows():
        measurements.append({
            "datetime": row['datetime'].isoformat(),
            "temperature": float(row['temp_smooth'])
        })

    if show_plot:
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(df_clean['datetime'], df_clean['temp_smooth'], color='red', linewidth=2.5, label='Temperature Trend')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=10))
        plt.xticks(rotation=45, ha='right')
        ax.yaxis.set_major_locator(plt.MaxNLocator(10))
        ax.tick_params(axis='both', which='major', labelsize=10)
        ax.set_xlabel('Date', fontsize=11, fontweight='bold')
        ax.set_ylabel('Temperature (°C)', fontsize=11, fontweight='bold')
        ax.set_title('Temperature Time Series', fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.legend(loc='best')
        plt.tight_layout()
        plt.show()

    return {
        "profiles": [{
            "profileId": 1,
            "measurements": measurements
        }]
    }
@mcp.tool
def argo_comparison_tool(
    datasets: List[List[Dict[str, Any]]],
    labels: List[str],
    variable: str,
    axis_var: Optional[str] = None
) -> Dict[str, Any]:
    """
    Compare statistical summaries and curve data for multiple ARGO datasets.

    Args:
        datasets: List of datasets (each dataset is a list of dictionaries).
        labels: List of dataset labels (same length as datasets).
        variable: The variable to compare ('temperature', 'salinity', or 'pressure').
        axis_var: Optional column to use for plotting curves (e.g., 'depth' or 'datetime').

    Returns:
        Dictionary with profiles for each dataset containing measurements
    """

    if len(datasets) != len(labels):
        raise ValueError("The number of datasets and labels must be equal.")

    # Create profiles list
    profiles = []
    
    for idx, (dataset, label) in enumerate(zip(datasets, labels)):
        df = pd.DataFrame(dataset)
        
        if variable not in df.columns:
            raise ValueError(f"'{variable}' not found in dataset '{label}'.")

        values = df[variable].dropna()
        
        # Create measurements for this profile
        measurements = [{
            "label": label,
            "variable": variable,
            "count": int(len(values)),
            "mean": float(np.mean(values)),
            "median": float(np.median(values)),
            "std_dev": float(np.std(values)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
        }]
        
        # Add curve data if axis_var is provided
        if axis_var and axis_var in df.columns:
            curve_df = df[[axis_var, variable]].dropna().sort_values(axis_var)
            for _, row in curve_df.iterrows():
                measurements.append({
                    axis_var: float(row[axis_var]),
                    variable: float(row[variable])
                })
        
        profiles.append({
            "profileId": idx + 1,
            "label": label,
            "measurements": measurements
        })

    return {"profiles": profiles}
@mcp.tool
def argo_salinity_trend(data: List[Dict[str, Any]], show_plot: bool = False, window: int = 20) -> Dict[str, List]:
    """
    Analyze salinity trends from ARGO data.
    
    Args:
        data: List of dictionaries with 'datetime' and 'salinity' keys
        show_plot: Whether to display a plot (default: False)
        window: Rolling window size for smoothing (default: 20)
    
    Returns:
        Dictionary with profiles containing measurements (datetime and salinity)
    """
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    if 'datetime' not in df.columns or 'salinity' not in df.columns:
        raise ValueError("Required columns: 'datetime', 'salinity'")

    # Create time-series with datetime index
    df_clean = df[['datetime', 'salinity']].dropna().copy()
    df_clean['datetime'] = pd.to_datetime(df_clean['datetime'])
    df_clean = df_clean.sort_values('datetime').set_index('datetime')
    
    # Calculate rolling average for smoothing
    df_clean['sal_smooth'] = df_clean['salinity'].rolling(window=window, center=True, min_periods=1).mean()
    df_clean = df_clean.reset_index()
    
    # Create measurements list
    measurements = []
    for _, row in df_clean.iterrows():
        measurements.append({
            "datetime": row['datetime'].isoformat(),
            "salinity": float(row['sal_smooth'])
        })

    if show_plot:
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(df_clean['datetime'], df_clean['sal_smooth'], color='blue', linewidth=2.5, label='Salinity Trend')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=10))
        plt.xticks(rotation=45, ha='right')
        ax.yaxis.set_major_locator(plt.MaxNLocator(10))
        ax.tick_params(axis='both', which='major', labelsize=10)
        ax.set_xlabel('Date', fontsize=11, fontweight='bold')
        ax.set_ylabel('Salinity (PSU)', fontsize=11, fontweight='bold')
        ax.set_title('Salinity Time Series', fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.legend(loc='best')
        plt.tight_layout()
        plt.show()

    return {
        "profiles": [{
            "profileId": 1,
            "measurements": measurements
        }]
    }
@mcp.tool
def argo_stat_summary(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute summary statistics for temperature, salinity, and pressure
    from ARGO data.

    Args:
        data: List of dictionaries containing at least 'temperature', 'salinity', 'pressure' keys.
              The data should already be filtered for region, depth, etc.

    Returns:
        Dictionary with profiles containing statistical measurements
    """
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Validate input columns
    required_cols = ['temperature', 'salinity', 'pressure']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column '{col}' in input data.")

    # Compute statistics and create measurements
    measurements = []
    for var in required_cols:
        values = df[var].dropna()
        measurements.append({
            "variable": var,
            "count": int(len(values)),
            "mean": float(np.mean(values)),
            "median": float(np.median(values)),
            "std_dev": float(np.std(values)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
        })

    return {
        "profiles": [{
            "profileId": 1,
            "measurements": measurements
        }]
    }
@mcp.tool
def argo_pressure_trend(data: List[Dict[str, Any]], show_plot: bool = False, window: int = 20) -> Dict[str, List]:
    """
    Analyze pressure trends from ARGO data.
    
    Args:
        data: List of dictionaries with 'datetime' and 'pressure' keys
        show_plot: Whether to display a plot (default: False)
        window: Rolling window size for smoothing (default: 20)
    
    Returns:
        Dictionary with profiles containing measurements (datetime and pressure)
    """
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    if 'datetime' not in df.columns or 'pressure' not in df.columns:
        raise ValueError("Required columns: 'datetime', 'pressure'")

    # Create time-series with datetime index
    df_clean = df[['datetime', 'pressure']].dropna().copy()
    df_clean['datetime'] = pd.to_datetime(df_clean['datetime'])
    df_clean = df_clean.sort_values('datetime').set_index('datetime')
    
    # Calculate rolling average for smoothing
    df_clean['press_smooth'] = df_clean['pressure'].rolling(window=window, center=True, min_periods=1).mean()
    df_clean = df_clean.reset_index()
    
    # Create measurements list
    measurements = []
    for _, row in df_clean.iterrows():
        measurements.append({
            "datetime": row['datetime'].isoformat(),
            "pressure": float(row['press_smooth'])
        })

    if show_plot:
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(df_clean['datetime'], df_clean['press_smooth'], color='green', linewidth=2.5, label='Pressure Trend')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=10))
        plt.xticks(rotation=45, ha='right')
        ax.yaxis.set_major_locator(plt.MaxNLocator(10))
        ax.tick_params(axis='both', which='major', labelsize=10)
        ax.set_xlabel('Date', fontsize=11, fontweight='bold')
        ax.set_ylabel('Pressure (dbar)', fontsize=11, fontweight='bold')
        ax.set_title('Pressure Time Series', fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.legend(loc='best')
        plt.tight_layout()
        plt.show()

    return {
        "profiles": [{
            "profileId": 1,
            "measurements": measurements
        }]
    }
@mcp.tool
def argo_ts_curve(data, show_plot: bool = False) -> Dict[str, List]:
    """
    Generate Temperature-Salinity (T-S) curve from ARGO data.
    
    Args:
        data: DataFrame or List of dictionaries with temperature and salinity columns
        show_plot: Whether to display a plot (default: False)
    
    Returns:
        Dictionary with profiles containing measurements (salinity and temperature)
    """
    # Convert to DataFrame if needed
    if isinstance(data, pd.DataFrame):
        df = data
    else:
        df = pd.DataFrame(data)
    
    # Get temperature and salinity columns
    temp_col = 'temperature' if 'temperature' in df.columns else 'TEMP'
    sal_col = 'salinity' if 'salinity' in df.columns else 'SAL'
    
    # Clean data - remove NaN values
    df_clean = df[[temp_col, sal_col]].dropna().copy()
    df_clean.columns = ['temperature', 'salinity']
    
    # Sort by salinity
    df_clean = df_clean.sort_values('salinity')
    
    # Create measurements list
    measurements = []
    for _, row in df_clean.iterrows():
        measurements.append({
            "salinity": float(row['salinity']),
            "temperature": float(row['temperature'])
        })
    
    if show_plot:
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Remove duplicate salinity values by averaging temperatures
        df_unique = df_clean.groupby('salinity')['temperature'].mean().reset_index()
        sal_unique = df_unique['salinity'].values
        temp_unique = df_unique['temperature'].values
        
        # Create smooth spline curve
        if len(sal_unique) > 3:
            from scipy.interpolate import UnivariateSpline
            smoothing_factor = len(sal_unique) * 0.01
            spline = UnivariateSpline(sal_unique, temp_unique, s=smoothing_factor, k=3)
            sal_smooth = np.linspace(sal_unique.min(), sal_unique.max(), 300)
            temp_smooth = spline(sal_smooth)
            ax.plot(sal_smooth, temp_smooth, 'b-', linewidth=2.5)
        else:
            ax.plot(sal_unique, temp_unique, 'b-', linewidth=2)
        
        ax.set_xlabel('Salinity (PSU)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Temperature (°C)', fontsize=12, fontweight='bold')
        ax.set_title('Temperature-Salinity (T-S) Diagram', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.xaxis.set_major_locator(plt.MaxNLocator(10))
        ax.yaxis.set_major_locator(plt.MaxNLocator(10))
        ax.tick_params(axis='both', which='major', labelsize=10)
        plt.tight_layout()
        plt.show()

    return {
        "profiles": [{
            "profileId": 1,
            "measurements": measurements
        }]
    }
@mcp.tool
def argo_td_curve(data: List[Dict[str, Any]], show_plot: bool = False) -> Dict[str, List]:
    """
    Generate Temperature-Depth (T-D) profile from ARGO data.
    
    Args:
        data: List of dictionaries with 'temperature' and 'level' keys
        show_plot: Whether to display a plot (default: False)
    
    Returns:
        Dictionary with profiles containing measurements (depth and temperature)
    """
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Get temperature and level columns
    temp_col = 'temperature' if 'temperature' in df.columns else 'TEMP'
    level_col = 'level' if 'level' in df.columns else 'LEVEL'
    
    if temp_col not in df.columns or level_col not in df.columns:
        raise ValueError(f"Required columns: '{temp_col}' and '{level_col}'")
    
    # Clean data - remove NaN values
    df_clean = df[[level_col, temp_col]].dropna().copy()
    df_clean.columns = ['level', 'temperature']
    
    # Convert level to pressure (dbar)
    pressure_levels = [5, 10, 20, 30, 50, 75, 100, 125, 150, 200, 250, 300, 400, 500, 
                      600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1750, 2000]
    
    def level_to_pressure(level):
        level_int = int(level)
        if level_int < len(pressure_levels):
            return pressure_levels[level_int]
        else:
            return pressure_levels[-1] + (level_int - len(pressure_levels) + 1) * 250
    
    df_clean['pressure'] = df_clean['level'].apply(level_to_pressure)
    
    # Convert pressure to depth using hydrostatic equation
    rho = 1025  # kg/m³ (Indian Ocean seawater density)
    g = 9.81    # m/s²
    df_clean['depth'] = df_clean['pressure'] * 10000 / (rho * g)
    
    # Sort by depth
    df_clean = df_clean.sort_values('depth')
    
    # Create measurements list
    measurements = []
    for _, row in df_clean.iterrows():
        measurements.append({
            "depth": float(row['depth']),
            "temperature": float(row['temperature']),
            "pressure": float(row['pressure'])
        })
    
    if show_plot:
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(df_clean['depth'], df_clean['temperature'], 'r-', linewidth=2.5)
        ax.set_xlabel('Depth (m)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Temperature (°C)', fontsize=12, fontweight='bold')
        ax.set_title('Temperature-Depth Profile', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.xaxis.set_major_locator(plt.MaxNLocator(10))
        ax.yaxis.set_major_locator(plt.MaxNLocator(10))
        ax.tick_params(axis='both', which='major', labelsize=10)
        plt.tight_layout()
        plt.show()
    
    return {
        "profiles": [{
            "profileId": 1,
            "measurements": measurements
        }]
    }

if __name__ == "__main__":
    mcp.run()