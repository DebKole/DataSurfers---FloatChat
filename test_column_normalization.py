"""
Quick test to verify column normalization is working
"""

from float_chat_mcp.data_access_tools.analysis_tools_wrapper import AnalysisToolsWrapper

# Create wrapper
wrapper = AnalysisToolsWrapper()

# Test data with database column names
test_data = [
    {
        "float_id": "1902482",
        "cycle_number": 1,
        "profile_datetime": "2025-01-01T00:00:00",
        "profile_latitude": 15.5,
        "profile_longitude": 77.5,
        "level": 0,
        "pressure": 10.0,
        "temperature": 25.5,
        "salinity": 35.2,
        "measurement_datetime": "2025-01-01T00:00:00"
    },
    {
        "float_id": "1902482",
        "cycle_number": 1,
        "profile_datetime": "2025-01-02T00:00:00",
        "profile_latitude": 15.6,
        "profile_longitude": 77.6,
        "level": 1,
        "pressure": 20.0,
        "temperature": 24.8,
        "salinity": 35.1,
        "measurement_datetime": "2025-01-02T00:00:00"
    },
    {
        "float_id": "1902482",
        "cycle_number": 1,
        "profile_datetime": "2025-01-03T00:00:00",
        "profile_latitude": 15.7,
        "profile_longitude": 77.7,
        "level": 2,
        "pressure": 30.0,
        "temperature": 24.2,
        "salinity": 35.0,
        "measurement_datetime": "2025-01-03T00:00:00"
    }
]

print("🧪 Testing Column Normalization")
print("=" * 50)
print(f"\n📥 Input columns: {list(test_data[0].keys())}")

# Normalize
normalized = wrapper._normalize_data(test_data)

print(f"📤 Output columns: {list(normalized[0].keys())}")

# Check if datetime column exists
if 'datetime' in normalized[0]:
    print("✅ SUCCESS: 'datetime' column found after normalization")
else:
    print("❌ FAIL: 'datetime' column NOT found")
    print(f"   Available columns: {list(normalized[0].keys())}")

# Check if temperature and salinity exist
if 'temperature' in normalized[0] and 'salinity' in normalized[0]:
    print("✅ SUCCESS: 'temperature' and 'salinity' columns found")
else:
    print("❌ FAIL: Missing temperature or salinity")

print("\n🧪 Testing temp_trend analysis...")
result = wrapper.execute_analysis("temp_trend", test_data)

if result.get("status") == "success":
    print("✅ SUCCESS: temp_trend analysis completed")
elif result.get("status") == "error":
    print(f"❌ FAIL: {result.get('error')}")
else:
    print(f"⚠️ UNKNOWN: {result}")

print("\n" + "=" * 50)
print("Test complete!")
