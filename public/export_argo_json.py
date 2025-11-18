import json
import psycopg2

conn = psycopg2.connect(
    host="",
    port=5432,
    dbname="january_data",
    user="postgres",
    password="pubgcodgerena123@",
)
def export_profiles_json(output_path: str):
    cur = conn.cursor()
    cur.execute("""
        SELECT
            m.global_profile_id,
            m.pressure,
            m.temperature,
            m.salinity
        FROM argo_measurements m
        ORDER BY m.global_profile_id, m.pressure
    """)

    rows = cur.fetchall()
    # rows: list of tuples (global_profile_id, pressure, temperature, salinity)

    profiles_map = {}
    for global_profile_id, pressure, temperature, salinity in rows:
        if global_profile_id not in profiles_map:
            profiles_map[global_profile_id] = {
                "profileId": global_profile_id,
                "measurements": [],
            }
        profiles_map[global_profile_id]["measurements"].append({
            "pressure": float(pressure),
            "temperature": float(temperature),
            "salinity": float(salinity),
        })

    profiles = list(profiles_map.values())

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=2)

    cur.close()
def export_trajectories_json(output_path: str):
    cur = conn.cursor()
    cur.execute("""
        SELECT
            global_profile_id AS profileId,
            float_id AS floatId,
            cycle_number AS cycleNumber,
            latitude AS lat,
            longitude AS lon,
            datetime
        FROM argo_profiles
        ORDER BY float_id, cycle_number
    """)

    rows = cur.fetchall()
    # rows: (profileId, floatId, cycleNumber, lat, lon, datetime)

    points = []
    for profile_id, float_id, cycle_number, lat, lon, dt in rows:
        points.append({
            "profileId": profile_id,
            "floatId": float_id,
            "cycleNumber": cycle_number,
            "lat": float(lat),
            "lon": float(lon),
            "datetime": dt.isoformat() if dt is not None else None,
        })

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(points, f, indent=2)

    cur.close()
if __name__ == "__main__":
    export_profiles_json("profiles_jan.json")
    export_trajectories_json("trajectories_jan.json")
    conn.close()