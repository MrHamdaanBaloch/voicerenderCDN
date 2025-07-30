#!/usr/bin/env bash
# exit on error
set -o errexit

# Define the model name and zip file
MODEL_NAME="vosk-model-small-en-us-0.15"
MODEL_ZIP="${MODEL_NAME}.zip"
MODEL_URL="https://alphacephei.com/vosk/models/${MODEL_ZIP}"

# Install system dependencies
apt-get update && apt-get install -y unzip wget

# Install Python dependencies
pip install -r requirements.txt

# Download and unzip the Vosk model only if it doesn't already exist
if [ ! -d "$MODEL_NAME" ]; then
  echo "Downloading Vosk model..."
  wget "$MODEL_URL"
  unzip "$MODEL_ZIP"
  rm "$MODEL_ZIP"
else
  echo "Vosk model already exists, skipping download."
fi
