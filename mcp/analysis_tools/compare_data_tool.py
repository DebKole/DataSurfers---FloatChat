from server import mcp
import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any

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
        {
            "comparison": {label: {stats...}},
            "curves": {label: {"x": [...], "y": [...]}}
        }
    """

    if len(datasets) != len(labels):
        raise ValueError("The number of datasets and labels must be equal.")

    # Compute statistics for each dataset
    summaries = {}
    curves = {}
    
    for dataset, label in zip(datasets, labels):
        df = pd.DataFrame(dataset)
        
        if variable not in df.columns:
            raise ValueError(f"'{variable}' not found in dataset '{label}'.")

        values = df[variable].dropna()
        summaries[label] = {
            "count": int(len(values)),
            "mean": float(np.mean(values)),
            "median": float(np.median(values)),
            "std_dev": float(np.std(values)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
        }

        # Prepare curve data if axis_var is provided
        if axis_var and axis_var in df.columns:
            curve_df = df[[axis_var, variable]].dropna().sort_values(axis_var)
            curves[label] = {
                "x": curve_df[axis_var].tolist(),
                "y": curve_df[variable].tolist(),
            }

    return {
        "comparison": summaries,
        "curves": curves
    }
