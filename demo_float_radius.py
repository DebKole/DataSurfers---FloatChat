#!/usr/bin/env python3
"""
Demo script to show floats within a specific radius
Useful for demonstrating trajectory prediction capabilities to judges
"""

from float_location_service import FloatLocationService
import json

def demo_radius_search():
    """Demonstrate finding floats within a radius"""
    
    print("=" * 70)
    print("ARGO FLOAT RADIUS SEARCH DEMO")
    print("Demonstrating float tracking within Indian Ocean")
    print("=" * 70)
    
    service = FloatLocationService()
    
    # Step 1: Get all Indian Ocean floats
    print("\n📍 Step 1: Finding all active floats in Indian Ocean...")
    all_floats = service.get_indian_ocean_floats(limit=100)
    print(f"   ✓ Found {len(all_floats)} active floats in January 2025 data")
    
    if not all_floats:
        print("   ⚠️  No floats found. Check your database connection.")
        return
    
    # Show sample floats
    print("\n   Sample floats:")
    for i, float_data in enumerate(all_floats[:5], 1):
        print(f"   {i}. Float {float_data['float_id']}: "
              f"({float_data['latitude']:.2f}°, {float_data['longitude']:.2f}°) "
              f"- {float_data['measurement_count']} measurements")
    
    # Step 2: Pick a center point and find floats within radius
    center_float = all_floats[0]
    center_lat = float(center_float['latitude'])
    center_lon = float(center_float['longitude'])
    
    print(f"\n📍 Step 2: Finding floats within 10km radius...")
    print(f"   Center point: Float {center_float['float_id']}")
    print(f"   Location: ({center_lat:.4f}°, {center_lon:.4f}°)")
    
    nearby_floats = service.get_floats_in_radius(
        center_lat=center_lat,
        center_lon=center_lon,
        radius_km=10,
        limit=50
    )
    
    print(f"\n   ✓ Found {len(nearby_floats)} floats within 10km:")
    for float_data in nearby_floats:
        print(f"   - Float {float_data['float_id']}: "
              f"{float_data['distance_km']:.2f}km away "
              f"({float_data['latitude']:.4f}°, {float_data['longitude']:.4f}°)")
    
    # Step 3: Demonstrate different radius sizes
    print(f"\n📍 Step 3: Comparing different radius sizes...")
    radii = [5, 10, 25, 50, 100]
    
    for radius in radii:
        floats_in_radius = service.get_floats_in_radius(
            center_lat=center_lat,
            center_lon=center_lon,
            radius_km=radius,
            limit=100
        )
        print(f"   {radius}km radius: {len(floats_in_radius)} floats")
    
    # Step 4: Show trajectory prediction potential
    print(f"\n🎯 Step 4: Trajectory Prediction Potential")
    print("   " + "=" * 60)
    print("   For judges demonstration:")
    print(f"   - Current position: ({center_lat:.4f}°, {center_lon:.4f}°)")
    print(f"   - Nearby floats: {len(nearby_floats)} within 10km")
    print("   - With trajectory data, we can:")
    print("     • Predict float movement patterns")
    print("     • Identify floats entering/leaving the region")
    print("     • Track ocean current patterns")
    print("     • Alert when floats approach specific zones")
    
    # Step 5: Export data for visualization
    print(f"\n💾 Step 5: Exporting data for map visualization...")
    
    export_data = {
        "center": {
            "lat": center_lat,
            "lon": center_lon,
            "float_id": center_float['float_id']
        },
        "radius_km": 10,
        "floats_in_radius": [
            {
                "float_id": f['float_id'],
                "latitude": float(f['latitude']),
                "longitude": float(f['longitude']),
                "distance_km": f['distance_km'],
                "datetime": str(f['datetime']),
                "measurements": f['measurement_count']
            }
            for f in nearby_floats
        ],
        "total_floats": len(nearby_floats)
    }
    
    # Save to JSON file
    with open('float_radius_demo.json', 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"   ✓ Data exported to: float_radius_demo.json")
    print(f"   ✓ Use this file to visualize floats on the map")
    
    # Step 6: Generate API URLs for frontend
    print(f"\n🌐 Step 6: API Endpoints for Frontend Integration")
    print("   " + "=" * 60)
    print(f"   Get Indian Ocean floats:")
    print(f"   → GET http://localhost:8000/floats/indian-ocean?limit=50")
    print(f"\n   Get floats within radius:")
    print(f"   → GET http://localhost:8000/floats/radius?lat={center_lat}&lon={center_lon}&radius=10")
    print(f"\n   Get specific float details:")
    print(f"   → GET http://localhost:8000/floats/{center_float['float_id']}")
    
    print("\n" + "=" * 70)
    print("✅ DEMO COMPLETE")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Start your backend: python app.py")
    print("2. Start your frontend: npm start")
    print("3. The map will now show real floats from your January 2025 database")
    print("4. Demonstrate to judges: 'These floats are within 10km of each other'")
    print("5. Explain: 'With trajectory data, we can predict their future positions'")
    print("=" * 70)


if __name__ == "__main__":
    demo_radius_search()
