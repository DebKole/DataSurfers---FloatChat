import pandas as pd
from sqlalchemy import create_engine
import matplotlib.pyplot as plt


from temp_trend_tool import argo_temp_trend
from salinity_trend_tool import argo_salinity_trend
from pressure_trend_tool import argo_pressure_trend
from statistical_summary import argo_stat_summary

print("imported")
# Replace these with your credentials
engine = create_engine("postgresql://postgres:[db_password]@localhost:5432/argo_db")
print("one")

# Example: select one profile worth of data
query = """
SELECT *
FROM argo_measurements 
ORDER BY datetime;
"""

df = pd.read_sql(query, engine)
print(df.head())
print(df.columns)

print("==="*40)
print("trends tools")

temp_result = argo_temp_trend(df, show_plot=True)
print("\nTemperature Trend Data Keys:", temp_result.keys())
print("First few X values:", temp_result['x'][:5])
print("First few Y values:", temp_result['y'][:5])

# 2️⃣ Salinity Trend
sal_result = argo_salinity_trend(df, show_plot=True)
print("\nSalinity Trend Data Keys:", sal_result.keys())

# 3️⃣ Pressure Trend
pres_result = argo_pressure_trend(df, show_plot=True)
print("\nPressure Trend Data Keys:", pres_result.keys())

# 4️⃣ Statistical Summary
stat_summary = argo_stat_summary(df)
print("\nStatistical Summary:")
print(stat_summary)

# --- (Optional) Combined plot for visual confirmation ---
plt.figure(figsize=(8,5))
plt.plot(temp_result['x'], temp_result['y'], 'r-', label='Temperature (°C)')
plt.plot(sal_result['x'], sal_result['y'], 'b-', label='Salinity (PSU)')
plt.plot(pres_result['x'], pres_result['y'], 'g-', label='Pressure (dbar)')
plt.xlabel("Datetime")
plt.legend()
plt.title("ARGO Trends from Profile 1")
plt.grid(True)
plt.show()

