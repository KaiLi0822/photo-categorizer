import logging
import os
import sys
import platform

# Detect if running as packaged executable
is_frozen = getattr(sys, 'frozen', False)

# Determine OS
is_windows = platform.system() == 'Windows'
is_mac = platform.system() == 'Darwin'

# Set log directory based on environment and OS
if is_frozen:
    if is_windows:
        # Windows packaged app: Use AppData\Local
        BASE_DIR = os.path.join(os.environ['LOCALAPPDATA'], 'PhotoCategorizer', 'Logs')
    elif is_mac:
        # macOS packaged app: Use ~/Library/Logs
        BASE_DIR = os.path.expanduser('~/Library/Logs/PhotoCategorizer')
    else:
        # Linux or other: Use ~/.photo_categorizer_logs
        BASE_DIR = os.path.expanduser('~/.photo_categorizer_logs')
else:
    if is_windows:
        # Windows dev mode: Use Documents\PhotoCategorizerLogs
        BASE_DIR = os.path.join(os.path.expanduser('~'), 'Documents', 'PhotoCategorizerLogs')
    else:
        # macOS/Linux dev mode: Use ~/.photo_categorizer_logs
        BASE_DIR = os.path.expanduser('~/.photo_categorizer_logs')

# Ensure the log directory exists
os.makedirs(BASE_DIR, exist_ok=True)

# Setup log file path and log level
LOG_PATH = os.path.join(BASE_DIR, "app.log")
LOG_LEVEL = logging.WARNING if is_frozen else logging.INFO

# Logging configuration
logging.basicConfig(
    level=LOG_LEVEL,  # Set to DEBUG for more verbose output
    format="%(asctime)s - %(levelname)s - [%(module)s] - %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, mode='a', encoding='utf-8'),  # Always log to file
        logging.StreamHandler(sys.stdout)  # Optional: log to console when possible
    ]
)

logger = logging.getLogger("PhotoCategorizer")
