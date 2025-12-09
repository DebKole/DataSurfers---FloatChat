# Test BGC Integration - Step by Step

## Step 1: Check if you have BGC files downloaded

```bash
ls -lh data/bgc_downloads/ | head -20
```

**Expected:** You should see `.nc` files

**If empty:** You need to download BGC files first (see Step 1b below)

### Step 1b: Download BGC files (if needed)

```bash
python3 bgc_download.py
```

OR check if you already have them:
```bash
find data/ -name "*.nc" -type f | grep -i bgc | head -10
```

---

## Step 2: Inspect what BGC parameters are available

```bash
python3 inspect_bgc_files.py
```

**Expected output:**
```
Found X NetCDF files

BGC Parameter Frequency:
  DOXY                : 120 files (80.0%)
  CHLA                :  95 files (63.3%)
  ...

Parameter Combinations:
  DOXY, CHLA, NITRATE : 65 files
  ...
```

**What this tells you:** Which BGC sensors are in your downloaded files

---

## Step 3: Check database connection

```bash
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

print('DB_HOST:', os.getenv('DB_HOST', 'localhost'))
print('DB_PORT:', os.getenv('DB_PORT', '5432'))
print('DB_USERNAME:', os.getenv('DB_USERNAME', 'postgres'))
print('DB_NAME:', os.getenv('DB_NAME', 'argo_bgc'))
print('DB_PASSWORD:', '***' if os.getenv('DB_PASSWORD') else 'NOT SET')
"
```

**Expected:** All values should be set, especially DB_PASSWORD

**If DB_PASSWORD is NOT SET:** Add it to your `.env` file:
```bash
echo "DB_PASSWORD=your_password_here" >> .env
```

---

## Step 4: Test database connection

```bash
python3 -c "
import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()

try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5432)),
        user=os.getenv('DB_USERNAME', 'postgres'),
        password=os.getenv('DB_PASSWORD'),
        database='postgres'  # Connect to default DB first
    )
    print('✅ Database connection successful!')
    conn.close()
except Exception as e:
    print(f'❌ Connection failed: {e}')
"
```

**Expected:** `✅ Database connection successful!`

---

## Step 5: Run the BGC integration test (DRY RUN)

This tests the schema without ingesting data:

```bash
python3 test_bgc_integration.py
```

**Expected output:**
```
Testing BGC Schema
✅ bgc_parameters column exists: jsonb
✅ GIN index exists: idx_bgc_parameters_gin

Testing BGC Query Patterns
  No data found (table may be empty)
  ✅ Query executed successfully (0 rows)

✅ All tests completed!
```

**If you see errors about missing table:** That's OK! The ingestion will create it.

---

## Step 6: Ingest a SMALL sample first (RECOMMENDED)

Let's test with just 5 files first:

```bash
python3 -c "
import os
import json

# Create a test config for just 5 files
config = {
    'index_url': 'https://data-argo.ifremer.fr/argo_bio-profile_index.txt',
    'base_url': 'https://data-argo.ifremer.fr/',
    'target_params': ['DOXY', 'CHLA', 'NITRATE'],
    'download_dir': './data/bgc_downloads/',
    'log_dir': './logs/',
    'max_total_files': 5,  # Just 5 files for testing!
    'skip_existing': True
}

with open('bgc_test_config.json', 'w') as f:
    json.dump(config, f, indent=2)

print('✅ Created bgc_test_config.json for testing')
"
```

Now run the ingestion with the test config:

```bash
python3 bgc_ingest.py --config bgc_test_config.json
```

**Expected output:**
```
Processing BGC files...
Downloaded: file1.nc
Processing file1.nc...
  Extracted X profiles and Y measurements
...
===== BGC INGEST SUMMARY =====
{
  "found": 5,
  "downloaded": 5,
  "processed_files": 5,
  "profiles": XX,
  "measurements": YYY
}
```

---

## Step 7: Verify the data was ingested

```bash
python3 -c "
import psycopg2
import os
import json
from dotenv import load_dotenv
load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    port=int(os.getenv('DB_PORT', 5432)),
    user=os.getenv('DB_USERNAME', 'postgres'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME', 'argo_bgc')
)

cur = conn.cursor()

# Count profiles
cur.execute('SELECT COUNT(*) FROM argo_bgc_profiles')
profile_count = cur.fetchone()[0]
print(f'✅ Profiles: {profile_count}')

# Count measurements
cur.execute('SELECT COUNT(*) FROM argo_bgc_measurements')
measurement_count = cur.fetchone()[0]
print(f'✅ Measurements: {measurement_count}')

# Count measurements with BGC data
cur.execute('SELECT COUNT(*) FROM argo_bgc_measurements WHERE bgc_parameters IS NOT NULL')
bgc_count = cur.fetchone()[0]
print(f'✅ Measurements with BGC data: {bgc_count}')

# Show available BGC parameters
cur.execute('''
    SELECT DISTINCT jsonb_object_keys(bgc_parameters) as parameter
    FROM argo_bgc_measurements
    WHERE bgc_parameters IS NOT NULL
''')
params = [row[0] for row in cur.fetchall()]
print(f'✅ Available BGC parameters: {params}')

# Show sample data
cur.execute('''
    SELECT 
        p.float_id,
        m.bgc_parameters
    FROM argo_bgc_profiles p
    JOIN argo_bgc_measurements m ON p.global_profile_id = m.global_profile_id
    WHERE m.bgc_parameters IS NOT NULL
    LIMIT 1
''')
result = cur.fetchone()
if result:
    print(f'\n✅ Sample data:')
    print(f'   Float ID: {result[0]}')
    print(f'   BGC Parameters: {json.dumps(result[1], indent=4)}')

conn.close()
"
```

**Expected output:**
```
✅ Profiles: 50
✅ Measurements: 2500
✅ Measurements with BGC data: 1200
✅ Available BGC parameters: ['DOXY', 'CHLA', 'NITRATE']

✅ Sample data:
   Float ID: 5906527
   BGC Parameters: {
       "DOXY": {
           "value": 245.3,
           "qc": 1
       },
       "CHLA": {
           "value": 0.52,
           "qc": 2
       }
   }
```

---

## Step 8: Test a BGC query

```bash
python3 -c "
import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    port=int(os.getenv('DB_PORT', 5432)),
    user=os.getenv('DB_USERNAME', 'postgres'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME', 'argo_bgc')
)

cur = conn.cursor()

# Test: List floats with DOXY
cur.execute('''
    SELECT DISTINCT p.float_id
    FROM argo_bgc_profiles p
    JOIN argo_bgc_measurements m ON p.global_profile_id = m.global_profile_id
    WHERE m.bgc_parameters ? 'DOXY'
    LIMIT 10
''')

floats = [row[0] for row in cur.fetchall()]
print(f'✅ Floats with DOXY measurements: {floats}')

# Test: Get DOXY values
cur.execute('''
    SELECT 
        p.float_id,
        (m.bgc_parameters->'DOXY'->>'value')::float as doxy_value,
        (m.bgc_parameters->'DOXY'->>'qc')::int as doxy_qc
    FROM argo_bgc_profiles p
    JOIN argo_bgc_measurements m ON p.global_profile_id = m.global_profile_id
    WHERE m.bgc_parameters ? 'DOXY'
      AND (m.bgc_parameters->'DOXY'->>'qc')::int <= 2
    LIMIT 5
''')

print(f'\n✅ Sample DOXY values (QC <= 2):')
for row in cur.fetchall():
    print(f'   Float {row[0]}: DOXY={row[1]:.2f}, QC={row[2]}')

conn.close()
"
```

**Expected output:**
```
✅ Floats with DOXY measurements: ['5906527', '5906528', '5906529']

✅ Sample DOXY values (QC <= 2):
   Float 5906527: DOXY=245.30, QC=1
   Float 5906527: DOXY=243.80, QC=1
   Float 5906528: DOXY=248.50, QC=2
```

---

## Step 9: Run full test suite

```bash
python3 test_bgc_integration.py
```

**Expected:** All tests should pass now with actual data

---

## Step 10: If everything works, ingest all files

```bash
# Remove the test config to use defaults
rm bgc_test_config.json

# Run full ingestion
python3 bgc_ingest.py
```

This will process all BGC files in `data/bgc_downloads/`

---

## Troubleshooting

### Problem: "No such file or directory: data/bgc_downloads"

**Solution:**
```bash
mkdir -p data/bgc_downloads
# Then download BGC files or copy them there
```

### Problem: "Database does not exist"

**Solution:**
```bash
# The script will create it automatically, but you can also:
createdb argo_bgc
```

### Problem: "Connection refused"

**Solution:**
- Check if PostgreSQL is running: `pg_isready`
- Check your `.env` file has correct credentials

### Problem: "No BGC parameters found"

**Solution:**
- Check if your NetCDF files actually have BGC data
- Run: `python3 inspect_bgc_files.py` to see what's available

### Problem: "Import error"

**Solution:**
```bash
pip install -r requirements.txt
# Or specifically:
pip install psycopg2-binary pandas numpy xarray netCDF4 python-dotenv
```

---

## Quick Verification Commands

```bash
# Check files
ls -lh data/bgc_downloads/ | wc -l

# Check database
psql -d argo_bgc -c "SELECT COUNT(*) FROM argo_bgc_measurements WHERE bgc_parameters IS NOT NULL;"

# Check logs
tail -f logs/bgc_ingest_*.log

# Check available parameters
psql -d argo_bgc -c "SELECT DISTINCT jsonb_object_keys(bgc_parameters) FROM argo_bgc_measurements WHERE bgc_parameters IS NOT NULL;"
```

---

## Success Criteria

✅ Files downloaded to `data/bgc_downloads/`  
✅ Database `argo_bgc` exists  
✅ Tables `argo_bgc_profiles` and `argo_bgc_measurements` exist  
✅ Column `bgc_parameters` is JSONB type  
✅ GIN index `idx_bgc_parameters_gin` exists  
✅ Data ingested (measurements with bgc_parameters IS NOT NULL)  
✅ Queries work (can extract DOXY, CHLA, etc.)  

---

**You're ready when all ✅ are green!**
