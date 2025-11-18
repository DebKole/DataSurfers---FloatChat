from server import mcp
import pandas as pd
from typing import Dict, List
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import UnivariateSpline
 # @mcp.tool
def argo_ts_curve(data, show_plot: bool = False) -> Dict[str, List]:
    """
    Generate Temperature-Salinity (T-S) curve from ARGO data.
    
    Args:
        data: DataFrame or List of dictionaries with temperature and salinity columns
        show_plot: Whether to display a plot (default: False)
    
    Returns:
        Dictionary with 'x' (salinity values) and 'y' (temperature values)
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
    
    # Extract x (salinity) and y (temperature)
    x = df_clean['salinity'].tolist()
    y = df_clean['temperature'].tolist()
    
    result = {"x": x, "y": y}
    if show_plot:
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Sort data by salinity
        df_sorted = df_clean.sort_values('salinity')
        
        # Remove duplicate salinity values by averaging temperatures
        df_unique = df_sorted.groupby('salinity')['temperature'].mean().reset_index()
        sal_unique = df_unique['salinity'].values
        temp_unique = df_unique['temperature'].values
        
        # Create smooth spline curve
        if len(sal_unique) > 3:
            smoothing_factor = len(sal_unique) * 0.01
            spline = UnivariateSpline(sal_unique, temp_unique, s=smoothing_factor, k=3)
            
            # Generate smooth curve
            sal_smooth = np.linspace(sal_unique.min(), sal_unique.max(), 300)
            temp_smooth = spline(sal_smooth)
            
            ax.plot(sal_smooth, temp_smooth, 'b-', linewidth=2.5)
        else:
            ax.plot(sal_unique, temp_unique, 'b-', linewidth=2)
        
        # Set axis labels and title
        ax.set_xlabel('Salinity (PSU)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Temperature (°C)', fontsize=12, fontweight='bold')
        ax.set_title('Temperature-Salinity (T-S) Diagram', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Format axis ticks for better readability
        ax.xaxis.set_major_locator(plt.MaxNLocator(10))
        ax.yaxis.set_major_locator(plt.MaxNLocator(10))
        ax.tick_params(axis='both', which='major', labelsize=10)
        
        # Add some padding to axis limits
        x_margin = (sal_unique.max() - sal_unique.min()) * 0.05
        y_margin = (temp_unique.max() - temp_unique.min()) * 0.05
        ax.set_xlim(sal_unique.min() - x_margin, sal_unique.max() + x_margin)
        ax.set_ylim(temp_unique.min() - y_margin, temp_unique.max() + y_margin)
        
        plt.tight_layout()
        plt.show()

    return result
