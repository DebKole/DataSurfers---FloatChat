from server import mcp
import pandas as pd
import numpy as np
from typing import Dict, List, Any

@mcp.tool
def argo_stat_summary(data: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    """
    Compute summary statistics for temperature, salinity, and pressure
    from ARGO data.

    Args:
        data: List of dictionaries containing at least 'temperature', 'salinity', 'pressure' keys.
              The data should already be filtered for region, depth, etc.

    Returns:
        Dictionary containing statistical summary of each variable.
    """
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Validate input columns
    required_cols = ['temperature', 'salinity', 'pressure']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column '{col}' in input data.")

    # Compute statistics
    summary_data = {}
    for var in required_cols:
        values = df[var].dropna()
        summary_data[var] = {
            "count": int(len(values)),
            "mean": float(np.mean(values)),
            "median": float(np.median(values)),
            "std_dev": float(np.std(values)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
        }

    return summary_data
