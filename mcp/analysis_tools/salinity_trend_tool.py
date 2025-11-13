from server import mcp
import pandas as pd
from typing import Dict, List
import matplotlib.pyplot as plt

@mcp.tool
def argo_salinity_trend(df: pd.DataFrame, show_plot: bool = False) -> Dict[str, List[float]]:
    if 'datetime' not in df.columns or 'salinity' not in df.columns:
        raise ValueError("Required columns: 'datetime', 'salinity'")

    data = df[['datetime', 'salinity']].dropna().sort_values('datetime')
    x = data['datetime'].tolist()
    y = data['salinity'].tolist()

    if show_plot:
        plt.plot(x, y, label="Salinity", color="blue")
        plt.xlabel("Julian Date")
        plt.ylabel("Salinity (PSU)")
        plt.title("Salinity Trend Over Time")
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    return {"x": x, "y": y}
