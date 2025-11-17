from server import mcp
import pandas as pd
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

@mcp.tool
def argo_salinity_trend(data: List[Dict[str, Any]], show_plot: bool = False, window: int = 20) -> Dict[str, List]:
    """
    Analyze salinity trends from ARGO data.
    
    Args:
        data: List of dictionaries with 'datetime' and 'salinity' keys
        show_plot: Whether to display a plot (default: False)
        window: Rolling window size for smoothing (default: 20)
    
    Returns:
        Dictionary with 'x' (datetimes) and 'y' (smoothed salinity values)
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
    
    x = [dt.isoformat() for dt in df_clean.index.tolist()]
    y = df_clean['sal_smooth'].tolist()

    if show_plot:
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(df_clean.index, df_clean['sal_smooth'], color='blue', linewidth=2.5, label='Salinity Trend')
        
        # Better date formatting
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=10))
        plt.xticks(rotation=45, ha='right')
        
        # Format y-axis
        ax.yaxis.set_major_locator(plt.MaxNLocator(10))
        ax.tick_params(axis='both', which='major', labelsize=10)
        
        ax.set_xlabel('Date', fontsize=11, fontweight='bold')
        ax.set_ylabel('Salinity (PSU)', fontsize=11, fontweight='bold')
        ax.set_title('Salinity Time Series', fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.legend(loc='best')
        plt.tight_layout()
        plt.show()

    return {"x": x, "y": y}
