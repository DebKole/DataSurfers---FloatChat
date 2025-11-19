#!/bin/bash

# FloatChat - Disable Live Automation
# Stops the hourly Argo data pipeline

echo "🛑 Disabling FloatChat Live Automation..."

# Check if cron job exists
if ! crontab -l 2>/dev/null | grep -q "run_live_pipeline.sh"; then
    echo "ℹ️  No automation found - already disabled"
    exit 0
fi

# Remove the cron job
crontab -l 2>/dev/null | grep -v "run_live_pipeline.sh" | crontab -

echo "✅ Live automation disabled!"
echo "💾 Storage usage will no longer increase automatically"
echo "🔄 To re-enable: ./scripts/enable_automation.sh"
echo "📊 Current data remains available for queries"