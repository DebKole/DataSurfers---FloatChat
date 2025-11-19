#!/bin/bash

# FloatChat Live Argo Data Automation Setup
# Sets up production automation system with real data downloads

set -e

echo "🌊 Setting up FloatChat Live Argo Data Automation..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}Project root: $PROJECT_ROOT${NC}"

# Create necessary directories
echo -e "${YELLOW}📁 Creating live data directories...${NC}"
mkdir -p "$PROJECT_ROOT/data/live_downloads"
mkdir -p "$PROJECT_ROOT/processed_data_live"
mkdir -p "$PROJECT_ROOT/logs"

# Make scripts executable
chmod +x "$SCRIPT_DIR/live_argo_pipeline.py"
chmod +x "$SCRIPT_DIR/setup_live_database.py"

echo -e "${YELLOW}🗄️  Setting up live database...${NC}"
python3 "$SCRIPT_DIR/setup_live_database.py"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to setup live database. Please check your PostgreSQL connection.${NC}"
    exit 1
fi

# Create live configuration
echo -e "${YELLOW}⚙️  Creating live pipeline configuration...${NC}"
python3 "$SCRIPT_DIR/live_argo_pipeline.py" --create-config

# Install additional required packages
echo -e "${YELLOW}📦 Installing additional Python dependencies...${NC}"
pip3 install beautifulsoup4 > /dev/null 2>&1 || {
    echo -e "${RED}❌ Failed to install beautifulsoup4. Please run:${NC}"
    echo "pip3 install beautifulsoup4"
    exit 1
}

# Create hourly cron job script
echo -e "${YELLOW}⏰ Creating hourly automation script...${NC}"
cat > "$SCRIPT_DIR/run_live_pipeline.sh" << EOF
#!/bin/bash
# Live Argo Data Pipeline - Runs hourly to check for new data

cd "$PROJECT_ROOT"
export PATH="\$PATH:/usr/local/bin:/usr/bin"

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Run the live pipeline
python3 "$SCRIPT_DIR/live_argo_pipeline.py" --config "$SCRIPT_DIR/live_pipeline_config.json"
EOF

chmod +x "$SCRIPT_DIR/run_live_pipeline.sh"

# Create manual test script
echo -e "${YELLOW}🧪 Creating test script...${NC}"
cat > "$SCRIPT_DIR/test_live_pipeline.sh" << EOF
#!/bin/bash
# Test the live pipeline without downloading files

echo "🧪 Testing Live Argo Pipeline Discovery..."
echo "========================================"
echo ""

cd "$PROJECT_ROOT"

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

echo "🔍 Checking for new files (dry run)..."
python3 "$SCRIPT_DIR/live_argo_pipeline.py" --config "$SCRIPT_DIR/live_pipeline_config.json" --dry-run

echo ""
echo "✅ Test completed! Check output above for discovered files."
EOF

chmod +x "$SCRIPT_DIR/test_live_pipeline.sh"

# Create production runner script
echo -e "${YELLOW}🚀 Creating production runner...${NC}"
cat > "$SCRIPT_DIR/run_live_production.sh" << EOF
#!/bin/bash
# Production Live Pipeline Runner

echo "🌊 FloatChat Live Argo Data Pipeline"
echo "===================================="
echo "🕐 Started at: \$(date)"
echo ""

cd "$PROJECT_ROOT"

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

echo "🔍 Checking IFREMER Argo database for new files..."
echo "📡 Monitoring November-December 2024 data..."
echo ""

# Run the live pipeline
python3 "$SCRIPT_DIR/live_argo_pipeline.py" --config "$SCRIPT_DIR/live_pipeline_config.json"

echo ""
echo "🕐 Completed at: \$(date)"
echo "📊 Check logs directory for detailed output."
EOF

chmod +x "$SCRIPT_DIR/run_live_production.sh"

# Create systemd service for production
echo -e "${YELLOW}🔧 Creating systemd service files...${NC}"
cat > "$SCRIPT_DIR/floatchat-live.service" << EOF
[Unit]
Description=FloatChat Live Argo Data Pipeline
After=network.target postgresql.service

[Service]
Type=oneshot
User=$USER
WorkingDirectory=$PROJECT_ROOT
ExecStart=$SCRIPT_DIR/run_live_pipeline.sh
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Create systemd timer for hourly execution
cat > "$SCRIPT_DIR/floatchat-live.timer" << EOF
[Unit]
Description=Run FloatChat Live Argo Pipeline every hour
Requires=floatchat-live.service

[Timer]
OnCalendar=hourly
Persistent=true
RandomizedDelaySec=300

[Install]
WantedBy=timers.target
EOF

# Create monitoring script
echo -e "${YELLOW}📊 Creating monitoring script...${NC}"
cat > "$SCRIPT_DIR/monitor_live_pipeline.sh" << EOF
#!/bin/bash
# Monitor the live pipeline status

cd "$PROJECT_ROOT"

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
ls -lt "$PROJECT_ROOT/logs/live_argo_pipeline_"*.log 2>/dev/null | head -5 || echo "No log files found"

echo ""
echo "💾 Disk Usage:"
echo "-------------"
du -sh "$PROJECT_ROOT/data/live_downloads" 2>/dev/null || echo "No live downloads directory"
du -sh "$PROJECT_ROOT/processed_data_live" 2>/dev/null || echo "No processed data directory"
EOF

chmod +x "$SCRIPT_DIR/monitor_live_pipeline.sh"

echo ""
echo -e "${GREEN}✅ Live automation setup complete!${NC}"
echo ""
echo -e "${PURPLE}🎯 LIVE PRODUCTION SYSTEM READY${NC}"
echo -e "${BLUE}================================${NC}"
echo ""
echo -e "${BLUE}📋 What was created:${NC}"
echo "  • Live database: floatchat_argo_live"
echo "  • Live pipeline: $SCRIPT_DIR/live_argo_pipeline.py"
echo "  • Configuration: $SCRIPT_DIR/live_pipeline_config.json"
echo "  • Hourly runner: $SCRIPT_DIR/run_live_pipeline.sh"
echo "  • Production runner: $SCRIPT_DIR/run_live_production.sh"
echo "  • Test script: $SCRIPT_DIR/test_live_pipeline.sh"
echo "  • Monitor script: $SCRIPT_DIR/monitor_live_pipeline.sh"
echo ""
echo -e "${BLUE}🧪 Test the system:${NC}"
echo "  ${YELLOW}./scripts/test_live_pipeline.sh${NC}     # Test file discovery"
echo "  ${YELLOW}./scripts/run_live_production.sh${NC}    # Run full pipeline once"
echo ""
echo -e "${BLUE}📊 Monitor the system:${NC}"
echo "  ${YELLOW}./scripts/monitor_live_pipeline.sh${NC}  # Check status and logs"
echo "  ${YELLOW}tail -f logs/live_argo_pipeline_*.log${NC}  # Watch live logs"
echo ""
echo -e "${BLUE}⏰ Set up hourly automation:${NC}"
echo ""
echo -e "${YELLOW}Option 1 - Cron (Simple):${NC}"
echo "  crontab -e"
echo "  Add: ${YELLOW}0 * * * * $SCRIPT_DIR/run_live_pipeline.sh${NC}"
echo ""
echo -e "${YELLOW}Option 2 - Systemd (Production):${NC}"
echo "  sudo cp $SCRIPT_DIR/floatchat-live.* /etc/systemd/system/"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl enable floatchat-live.timer"
echo "  sudo systemctl start floatchat-live.timer"
echo "  sudo systemctl status floatchat-live.timer"
echo ""
echo -e "${GREEN}🌊 Your FloatChat system now has LIVE oceanographic data automation!${NC}"
echo -e "${GREEN}📡 It will automatically download and process new Argo data every hour.${NC}"