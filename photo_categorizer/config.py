# Backend Configuration
BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 5050

# API URLs (constructed using host/port)
BASE_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}/"

# Backend File
BACKEND_FILE_PATH:str = "backend/backend.py"  # Relative path to backend file

# Model Score
THRESHOLD = 22
