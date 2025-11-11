#!/bin/bash
# Test the live pipeline without downloading files

echo "🧪 Testing Live Argo Pipeline Discovery..."
echo "========================================"
echo ""

cd "/home/satakucodes/Desktop/Coding/SIH/DataSurfers---FloatChat"

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

echo "🔍 Checking for new files (dry run)..."
python3 "/home/satakucodes/Desktop/Coding/SIH/DataSurfers---FloatChat/scripts/live_argo_pipeline.py" --config "/home/satakucodes/Desktop/Coding/SIH/DataSurfers---FloatChat/scripts/live_pipeline_config.json" --dry-run

echo ""
echo "✅ Test completed! Check output above for discovered files."
