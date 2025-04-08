import os
import json
from dotenv import load_dotenv

load_dotenv()

CLASS_NAME = "CLIPS"
VERSION = "0.1.0"
APP_NAME = "Copywriter's Lightweight Iteration Pipeline System"

DEBUG = os.getenv("DEBUG", "false").lower() == "true"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

DEFAULT_MODEL = "gpt-4o"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
SESSIONS_DIR = os.path.join(BASE_DIR, "sessions")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

def ensure_directories():
    """Ensure all required directories exist"""
    for directory in [LOGS_DIR, SESSIONS_DIR, OUTPUT_DIR]:
        os.makedirs(directory, exist_ok=True)

def get_openai_api_key():
    """Get the OpenAI API key from environment variable"""
    return OPENAI_API_KEY

def save_openai_api_key(api_key):
    """Save the OpenAI API key to environment variable or configuration"""
    # In a production app, we'd use a more secure storage method
    # For now, we'll just update the environment variable
    os.environ["OPENAI_API_KEY"] = api_key
    global OPENAI_API_KEY
    OPENAI_API_KEY = api_key
    return True

def get_app_settings():
    """Get the application settings for the frontend"""
    return {
        "appName": APP_NAME,
        "version": VERSION,
        "debugMode": DEBUG,
        "hasApiKey": bool(OPENAI_API_KEY),
        "defaultModel": DEFAULT_MODEL
    }
