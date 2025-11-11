#!/bin/bash
# Production Live Pipeline Runner

echo "🌊 FloatChat Live Argo Data Pipeline"
echo "===================================="
echo "🕐 Started at: $(date)"
echo ""

cd "/home/satakucodes/Desktop/Coding/SIH/DataSurfers---FloatChat"

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

echo "🔍 Checking IFREMER Argo database for new files..."
echo "📡 Monitoring November-December 2024 data..."
echo ""

# Run the live pipeline
python3 "/home/satakucodes/Desktop/Coding/SIH/DataSurfers---FloatChat/scripts/live_argo_pipeline.py" --config "/home/satakucodes/Desktop/Coding/SIH/DataSurfers---FloatChat/scripts/live_pipeline_config.json"

echo ""
echo "🕐 Completed at: $(date)"
echo "📊 Check logs directory for detailed output."
