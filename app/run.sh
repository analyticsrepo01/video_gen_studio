#!/bin/bash

# Video Generation Studio - Startup Script

echo "🎬 Starting Video Generation Studio..."

# Check if FFmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  FFmpeg not found. Installing..."
    if command -v apt &> /dev/null; then
        sudo apt update && sudo apt install -y ffmpeg
    elif command -v brew &> /dev/null; then
        brew install ffmpeg
    else
        echo "❌ Please install FFmpeg manually"
        exit 1
    fi
fi

# Check if Python packages are installed
echo "📦 Checking Python dependencies..."
pip install -r requirements.txt

# Create output directories
echo "📁 Creating output directories..."
mkdir -p output/videos
mkdir -p output/images
mkdir -p temp

# Check Google Cloud credentials
if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "⚠️  GOOGLE_APPLICATION_CREDENTIALS not set"
    echo "Please set your service account key file path:"
    echo "export GOOGLE_APPLICATION_CREDENTIALS=\"path/to/your/service-account-key.json\""
fi

echo "🚀 Starting the application..."
echo ""
python app.py