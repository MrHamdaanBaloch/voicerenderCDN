# app/core/config.py
import os
from dotenv import load_dotenv

def load_config():
    """
    Loads configuration from environment variables, validates required ones,
    and returns them in a dictionary.
    """
    load_dotenv()

    config = {
        # SignalWire Configuration
        "SIGNALWIRE_PROJECT_ID": os.getenv("SIGNALWIRE_PROJECT_ID"),
        "SIGNALWIRE_API_TOKEN": os.getenv("SIGNALWIRE_API_TOKEN"),
        "SIGNALWIRE_SPACE_URL": os.getenv("SIGNALWIRE_SPACE_URL"),
        "SIGNALWIRE_CONTEXT": os.getenv("SIGNALWIRE_CONTEXT", "voiceai"),

        # AI Model Paths (Local)
        "PIPER_MODEL_PATH": os.getenv("PIPER_MODEL_PATH", "./piper_models/en_US-lessac-medium.onnx"),
        "PIPER_CONFIG_PATH": os.getenv("PIPER_CONFIG_PATH", "./piper_models/en_US-lessac-medium.onnx.json"),

        # AI Model Configuration
        "LLM_MODEL": os.getenv("LLM_MODEL", "llama3-8b-8192"),
        "GROQ_API_KEY": os.getenv("GROQ_API_KEY"),

        # Redis Configuration
        "REDIS_URL": os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    }

    # Ensure critical variables are set
    required_vars = [
        "SIGNALWIRE_PROJECT_ID", "SIGNALWIRE_API_TOKEN", "SIGNALWIRE_SPACE_URL",
        "GROQ_API_KEY"
    ]
    for var in required_vars:
        if not config.get(var):
            raise ValueError(f"Missing required environment variable: {var}")

    return config

# For any modules that still import these as global constants,
# we can load them once here. This is a transitional step.
# A better long-term solution is for modules to call load_config() themselves.
_config = load_config()
SIGNALWIRE_PROJECT_ID = _config["SIGNALWIRE_PROJECT_ID"]
SIGNALWIRE_API_TOKEN = _config["SIGNALWIRE_API_TOKEN"]
SIGNALWIRE_SPACE_URL = _config["SIGNALWIRE_SPACE_URL"]
SIGNALWIRE_CONTEXT = _config["SIGNALWIRE_CONTEXT"]
PIPER_MODEL_PATH = _config["PIPER_MODEL_PATH"]
PIPER_CONFIG_PATH = _config["PIPER_CONFIG_PATH"]
LLM_MODEL = _config["LLM_MODEL"]
GROQ_API_KEY = _config["GROQ_API_KEY"]
REDIS_URL = _config["REDIS_URL"]
