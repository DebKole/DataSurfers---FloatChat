#!/bin/bash
# Live Argo Data Pipeline - Runs hourly to check for new data

cd "/home/satakucodes/Desktop/Coding/SIH/DataSurfers---FloatChat"
export PATH="$PATH:/usr/local/bin:/usr/bin"

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Run the live pipeline
python3 "/home/satakucodes/Desktop/Coding/SIH/DataSurfers---FloatChat/scripts/live_argo_pipeline.py" --config "/home/satakucodes/Desktop/Coding/SIH/DataSurfers---FloatChat/scripts/live_pipeline_config.json"
