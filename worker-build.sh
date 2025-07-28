#!/usr/bin/env bash
# exit on error
set -o errexit

# Install system dependencies for unzip
apt-get update && apt-get install -y unzip

# Install Python dependencies
pip install -r requirements.txt

# Download and unzip the Vosk model
wget https://alphacephei.com/vosk/models/vosk-model-en-us-0.22-lgraph.zip
unzip vosk-model-en-us-0.22-lgraph.zip
