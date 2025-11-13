from server import mcp
import pandas as pd
from typing import Dict, List
import matplotlib.pyplot as plt

@mcp.tool
def argo_temp_trend(df: pd.DataFrame, show_plot: bool = False) -> Dict[str, List[float]]:
    if 'datetime' not in df.columns or 'temperature' not in df.columns:
        raise ValueError("Required columns: 'datetime', 'temperature'")

    data = df[['datetime', 'temperature']].dropna().sort_values('datetime')
    x = data['datetime'].tolist()
    y = data['temperature'].tolist()

    if show_plot:
        plt.plot(x, y, label="Temperature", color="red")
        plt.xlabel("Date & Time")
        plt.ylabel("Temperature (°C)")
        plt.title("Temperature Trend Over Time")
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    return {"x": x, "y": y}
