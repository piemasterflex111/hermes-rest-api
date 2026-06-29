"""Configuration for Hermes REST API."""
import os

# Server configuration
HOST = os.getenv("HERMES_API_HOST", "0.0.0.0")
PORT = int(os.getenv("HERMES_API_PORT", "8090"))

# Session configuration
SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", "3600"))  # 1 hour
MAX_SESSIONS = int(os.getenv("MAX_SESSIONS", "10"))
SESSION_DIR = os.getenv("SESSION_DIR", os.path.join(os.path.expanduser("~"), ".hermes-rest-api", "sessions"))

# Hermes CLI path
HERMES_CLI = os.getenv("HERMES_CLI", "hermes")
HERMES_CLI_ARGS = ["--cli"]  # Default arguments for hermes CLI

# API key authentication
API_KEYS_FILE = os.getenv("API_KEYS_FILE", os.path.join(os.path.expanduser("~"), ".hermes-rest-api", "keys.json"))

# Sandboxing
SANDBOX_ENABLED = os.getenv("SANDBOX_ENABLED", "true").lower() == "true"
SANDBOX_ALLOWED_DIRS = [os.path.expanduser("~")]
SANDBOX_DENIED_COMMANDS = ["rm -rf", "sudo", "mkfs", "dd", "fdisk"]

# Streaming
STREAM_BUFFER_SIZE = 8192
STREAM_FLUSH_INTERVAL = 0.1  # seconds
