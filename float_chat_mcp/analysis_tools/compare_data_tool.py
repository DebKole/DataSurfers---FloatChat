from server import mcp
import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any

@mcp.tool
def argo_comparison_tool(
    dfs: List[pd.DataFrame],
    labels: List[str],
    variable: str,
    axis_var: Optional[str] = None
) -> Dict[str, Any]:
    """
    Compare statistical summaries and curve data for multiple ARGO datasets.

    Args:
        dfs: List of pre-filtered pandas DataFrames (same structure, e.g. same variable column).
        labels: List of dataset labels (same length as dfs).
        variable: The variable to compare ('temperature', 'salinity', or 'pressure').
        axis_var: Optional column to use for plotting curves (e.g., 'depth' or 'time').

    Returns:
        {
            "comparison_df": <DataFrame summarizing stats across datasets>,
            "curves": {
                label1: {"x": [...], "y": [...]},
                label2: {"x": [...], "y": [...]},
                ...
            }
        }
    """

    if len(dfs) != len(labels):
        raise ValueError("The number of DataFrames and labels must be equal.")

    # --- Compute statistics for each dataset ---
    summaries = {}
    for df, label in zip(dfs, labels):
        if variable not in df.columns:
            raise ValueError(f"'{variable}' not found in DataFrame '{label}'.")

        data = df[variable].dropna()
        summaries[label] = {
            "count": len(data),
            "mean": np.mean(data),
            "median": np.median(data),
            "std_dev": np.std(data),
            "min": np.min(data),
            "max": np.max(data),
        }

    comparison_df = pd.DataFrame(summaries).T.round(4)
    comparison_df.index.name = "Dataset"

    # --- Prepare curve data (for visualization tool) ---
    curves = {}
    if axis_var and all(axis_var in df.columns for df in dfs):
        for df, label in zip(dfs, labels):
            curve_df = df[[axis_var, variable]].dropna().sort_values(axis_var)
            curves[label] = {
                "x": curve_df[axis_var].tolist(),
                "y": curve_df[variable].tolist(),
            }

    return {
        "comparison_df": comparison_df,
        "curves": curves
    }
