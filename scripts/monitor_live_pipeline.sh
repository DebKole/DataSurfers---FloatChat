#!/bin/bash
# Monitor the live pipeline status

cd "/home/satakucodes/Desktop/Coding/SIH/DataSurfers---FloatChat"

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

echo "📊 FloatChat Live Pipeline Status"
echo "================================="
echo ""

# Check database connection
python3 -c "
import psycopg2
from scripts.setup_live_database import get_live_db_config

try:
    conn = psycopg2.connect(**get_live_db_config())
    cursor = conn.cursor()
    
    # Get latest automation runs
    cursor.execute('''
        SELECT run_timestamp, status, files_downloaded, profiles_added, 
               measurements_added, duration_seconds, error_message
        FROM automation_log 
        ORDER BY run_timestamp DESC 
        LIMIT 10
    ''')
    
    runs = cursor.fetchall()
    
    print('📈 Recent Pipeline Runs:')
    print('-' * 80)
    for run in runs:
        timestamp, status, files, profiles, measurements, duration, error = run
        status_icon = '✅' if status == 'completed' else '❌' if status == 'error' else '🔄'
        print(f'{status_icon} {timestamp} | {status} | Files: {files or 0} | Profiles: {profiles or 0} | Duration: {duration or 0:.1f}s')
        if error:
            print(f'   Error: {error}')
    
    # Get current data stats
    cursor.execute('SELECT COUNT(*) FROM argo_profiles')
    total_profiles = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM argo_measurements')
    total_measurements = cursor.fetchone()[0]
    
    cursor.execute('SELECT MAX(datetime) FROM argo_profiles WHERE datetime IS NOT NULL')
    latest_data = cursor.fetchone()[0]
    
    print('')
    print('📊 Current Database Status:')
    print('-' * 40)
    print(f'Total Profiles: {total_profiles:,}')
    print(f'Total Measurements: {total_measurements:,}')
    print(f'Latest Data: {latest_data}')
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f'❌ Error connecting to live database: {e}')
"

echo ""
echo "📁 Recent Log Files:"
echo "-------------------"
ls -lt "/home/satakucodes/Desktop/Coding/SIH/DataSurfers---FloatChat/logs/live_argo_pipeline_"*.log 2>/dev/null | head -5 || echo "No log files found"

echo ""
echo "💾 Disk Usage:"
echo "-------------"
du -sh "/home/satakucodes/Desktop/Coding/SIH/DataSurfers---FloatChat/data/live_downloads" 2>/dev/null || echo "No live downloads directory"
du -sh "/home/satakucodes/Desktop/Coding/SIH/DataSurfers---FloatChat/processed_data_live" 2>/dev/null || echo "No processed data directory"
