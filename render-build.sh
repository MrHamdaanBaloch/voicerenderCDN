#!/usr/bin/env bash
# exit on error
set -o errexit

# Install system dependencies for ffmpeg
apt-get update && apt-get install -y ffmpeg

# Install Python dependencies from both files
pip install -r tts_requirements.txt
pip install -r requirements.txt
