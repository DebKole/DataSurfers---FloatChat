import pandas as pd
from sqlalchemy import create_engine
import matplotlib.pyplot as plt


import server

# Access the actual functions from the decorated tools
argo_temp_trend = server.argo_temp_trend.fn
argo_td_curve = server.argo_td_curve.fn
argo_salinity_trend = server.argo_salinity_trend.fn
argo_pressure_trend = server.argo_pressure_trend.fn
argo_stat_summary = server.argo_stat_summary.fn
argo_ts_curve = server.argo_ts_curve.fn
argo_comparison_tool = server.argo_comparison_tool.fn

print("imported")
# Replace these with your credentials
engine = create_engine("postgresql://postgres:pubgcodgerena123@@localhost:5432/argo_db")
print("one")

# Example: select ONE SINGLE profile worth of data
query = """
SELECT
    p.float_id,
    p.global_profile_id,
    DATE(m.datetime) AS day,
    m.level,
    m.pressure,
    m.temperature,
    m.salinity,
    m.latitude,
    m.longitude,
    m.datetime
FROM argo_profiles p
JOIN argo_measurements m
    ON m.global_profile_id = p.global_profile_id
WHERE p.float_id = '5906527'
ORDER BY p.global_profile_id, m.level
LIMIT 30;



"""

df = pd.read_sql(query, engine)
print(df.head())
print(df.columns)

print("==="*40)
print("trends tools")

temp_result = argo_temp_trend(df.to_dict('records'), show_plot=True)
print("\nTemperature Trend Data Keys:", temp_result.keys())
measurements = temp_result['profiles'][0]['measurements']
print(f"Number of measurements: {len(measurements)}")
print("First few measurements:", measurements[:3])

# 2️⃣ Salinity Trend
sal_result = argo_salinity_trend(df.to_dict('records'), show_plot=True)
print("\nSalinity Trend Data Keys:", sal_result.keys())
measurements = sal_result['profiles'][0]['measurements']
print(f"Number of measurements: {len(measurements)}")
print("First few measurements:", measurements[:3])

# 3️⃣ Pressure Trend
pres_result = argo_pressure_trend(df.to_dict('records'), show_plot=True)
print("\nPressure Trend Data Keys:", pres_result.keys())
measurements = pres_result['profiles'][0]['measurements']
print(f"Number of measurements: {len(measurements)}")
print("First few measurements:", measurements[:3])

# 4️⃣ Statistical Summary
stat_summary = argo_stat_summary(df.to_dict('records'))
print("\nStatistical Summary:")
print(stat_summary)
measurements = stat_summary['profiles'][0]['measurements']
for m in measurements:
    print(f"{m['variable']}: mean={m['mean']:.2f}, std={m['std_dev']:.2f}, min={m['min']:.2f}, max={m['max']:.2f}")

# 5️⃣ T-S Curve
print("\n" + "==="*40)
print("T-S Curve Tool")
ts_result = argo_ts_curve(df.to_dict('records'), show_plot=True)
print("\nT-S Curve Data Keys:", ts_result.keys())
measurements = ts_result['profiles'][0]['measurements']
print(f"Number of measurements: {len(measurements)}")
print("First few measurements:", measurements[:3])

# 6️⃣ T-D Curve (Temperature-Depth Profile)
print("\n" + "==="*40)
print("T-D Curve Tool (Temperature-Depth Profile)")
print(f"Number of rows in dataframe: {len(df)}")
print(f"Unique profiles: {df['global_profile_id'].nunique()}")
print(f"Level range: {df['level'].min()} to {df['level'].max()}")
print(f"Temperature range: {df['temperature'].min():.2f} to {df['temperature'].max():.2f}")
td_result = argo_td_curve(df.to_dict('records'), show_plot=True)
print("\nT-D Curve Data Keys:", td_result.keys())
measurements = td_result['profiles'][0]['measurements']
print(f"Number of measurements: {len(measurements)}")
print("First few measurements:", measurements[:3])
depths = [m['depth'] for m in measurements]
print(f"Depth range: {min(depths):.2f} to {max(depths):.2f} meters")



