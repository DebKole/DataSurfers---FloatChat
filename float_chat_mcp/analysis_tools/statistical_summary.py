from server import mcp
import pandas as pd
import numpy as np

@mcp.tool
def argo_stat_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute summary statistics for temperature, salinity, and pressure
    from a pre-filtered ARGO dataframe.

    Args:
        df: Pandas DataFrame containing at least ['temperature', 'salinity', 'pressure'] columns.
             The data should already be filtered for region, depth, etc.

    Returns:
        summary_df: DataFrame containing statistical summary of each variable.
    """

    # --- Validate input columns ---
    required_cols = ['temperature', 'salinity', 'pressure']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column '{col}' in input DataFrame.")

    # --- Compute statistics ---
    summary_data = {}
    for var in required_cols:
        data = df[var].dropna()
        summary_data[var] = {
            "count": len(data),
            "mean": np.mean(data),
            "median": np.median(data),
            "std_dev": np.std(data),
            "min": np.min(data),
            "max": np.max(data),
        }

    # --- Convert to DataFrame for easy display ---
    summary_df = pd.DataFrame(summary_data).T  # transpose so variables are rows
    summary_df = summary_df.round(4)  # format nicely

    return summary_df
