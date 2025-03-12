import logging
import os
import sys

# Detect if running as packaged executable
is_frozen = getattr(sys, 'frozen', False)

# Set log directory based on environment
if is_frozen:
    # When packaged, log into user Library/Logs
    BASE_DIR = os.path.expanduser('~/Library/Logs/PhotoCategorizer')
else:
    # When running as script, log into home directory under custom folder
    BASE_DIR = os.path.expanduser('~/.photo_categorizer_logs')

# Ensure the log directory exists
os.makedirs(BASE_DIR, exist_ok=True)
LOG_PATH = os.path.join(BASE_DIR, "app.log")
LOG_LEVEL = logging.WARNING if is_frozen else logging.INFO
# Logging configuration
logging.basicConfig(
    level=LOG_LEVEL,  # You can set to DEBUG for more verbose output
    format="%(asctime)s - %(levelname)s - [%(module)s] - %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, mode='a'),  # Always log to file
        logging.StreamHandler(sys.stdout)  # Optional: log to console when possible
    ]
)

logger = logging.getLogger("PhotoCategorizer")
