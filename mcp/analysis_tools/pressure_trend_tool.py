from server import mcp
import pandas as pd
from typing import Dict, List
import matplotlib.pyplot as plt

@mcp.tool
def argo_pressure_trend(df: pd.DataFrame, show_plot: bool = False) -> Dict[str, List[float]]:
    if 'datetime' not in df.columns or 'pressure' not in df.columns:
        raise ValueError("Required columns: 'datetime', 'pressure'")

    data = df[['datetime', 'pressure']].dropna().sort_values('datetime')
    x = data['datetime'].tolist()
    y = data['pressure'].tolist()

    if show_plot:
        plt.plot(x, y, label="Pressure", color="green")
        plt.xlabel("Julian Date")
        plt.ylabel("Pressure (dbar)")
        plt.title("Pressure Trend Over Time")
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    return {"x": x, "y": y}
