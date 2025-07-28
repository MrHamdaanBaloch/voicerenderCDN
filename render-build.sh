#!/usr/bin/env bash
# exit on error
set -o errexit

# Install system dependencies for ffmpeg and unzip
apt-get update && apt-get install -y ffmpeg unzip

# Install Python dependencies from both files
pip install -r tts_requirements.txt
pip install -r requirements.txt

# Download and unzip the Vosk model for the Celery worker
wget https://alphacephei.com/vosk/models/vosk-model-en-us-0.22-lgraph.zip
unzip vosk-model-en-us-0.22-lgraph.zip
