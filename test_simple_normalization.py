"""
Simple test for column normalization
"""

# Test the column mappings directly
column_mappings = {
    # Uppercase mappings
    'TEMP': 'temperature',
    'SAL': 'salinity',
    'PRES': 'pressure',
    'DATETIME': 'datetime',
    'LEVEL': 'level',
    'DEPTH': 'depth',
    # Database-specific mappings (lowercase)
    'profile_datetime': 'datetime',
    'measurement_datetime': 'datetime',
    'profile_latitude': 'latitude',
    'profile_longitude': 'longitude'
}

# Test data
test_row = {
    "float_id": "1902482",
    "profile_datetime": "2025-01-01T00:00:00",
    "temperature": 25.5,
    "salinity": 35.2
}

print("🧪 Testing Column Normalization Logic")
print("=" * 50)
print(f"\nInput columns: {list(test_row.keys())}")

# Normalize
normalized_row = {}
for key, value in test_row.items():
    lower_key = key.lower()
    
    # Check mappings
    if key in column_mappings:
        lower_key = column_mappings[key]
        print(f"  ✅ Mapped '{key}' -> '{lower_key}' (exact match)")
    elif lower_key in column_mappings:
        lower_key = column_mappings[lower_key]
        print(f"  ✅ Mapped '{key}' -> '{lower_key}' (lowercase match)")
    elif key.upper() in column_mappings:
        lower_key = column_mappings[key.upper()]
        print(f"  ✅ Mapped '{key}' -> '{lower_key}' (uppercase match)")
    else:
        print(f"  ➡️ Kept '{key}' as '{lower_key}' (no mapping)")
    
    normalized_row[lower_key] = value

print(f"\nOutput columns: {list(normalized_row.keys())}")

# Check results
if 'datetime' in normalized_row:
    print("\n✅ SUCCESS: 'datetime' column exists!")
else:
    print("\n❌ FAIL: 'datetime' column missing!")

print("\nNormalized data:")
for k, v in normalized_row.items():
    print(f"  {k}: {v}")
