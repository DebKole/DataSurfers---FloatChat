from server import mcp
import pandas as pd
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

@mcp.tool
def argo_pressure_trend(data: List[Dict[str, Any]], show_plot: bool = False, window: int = 20) -> Dict[str, List]:
    """
    Analyze pressure trends from ARGO data.
    
    Args:
        data: List of dictionaries with 'datetime' and 'pressure' keys
        show_plot: Whether to display a plot (default: False)
        window: Rolling window size for smoothing (default: 20)
    
    Returns:
        Dictionary with 'x' (datetimes) and 'y' (smoothed pressure values)
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
    
    x = [dt.isoformat() for dt in df_clean.index.tolist()]
    y = df_clean['press_smooth'].tolist()

    if show_plot:
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(df_clean.index, df_clean['press_smooth'], color='green', linewidth=2.5, label='Pressure Trend')
        
        # Better date formatting
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=10))
        plt.xticks(rotation=45, ha='right')
        
        # Format y-axis
        ax.yaxis.set_major_locator(plt.MaxNLocator(10))
        ax.tick_params(axis='both', which='major', labelsize=10)
        
        ax.set_xlabel('Date', fontsize=11, fontweight='bold')
        ax.set_ylabel('Pressure (dbar)', fontsize=11, fontweight='bold')
        ax.set_title('Pressure Time Series', fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.legend(loc='best')
        plt.tight_layout()
        plt.show()

    return {"x": x, "y": y}
