#!/bin/bash

# FloatChat - Enable Live Automation
# Re-enables the hourly Argo data pipeline

echo "🔄 Enabling FloatChat Live Automation..."

# Get the current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Add cron job for hourly execution
CRON_JOB="0 * * * * $PROJECT_DIR/scripts/run_live_pipeline.sh"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "run_live_pipeline.sh"; then
    echo "⚠️  Automation is already enabled"
    exit 0
fi

# Add the cron job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "✅ Live automation enabled!"
echo "📊 Pipeline will run every hour at minute 0"
echo "📝 To disable: crontab -r"
echo "📈 To monitor: ./scripts/monitor_live_pipeline.sh"