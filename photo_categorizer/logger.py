import logging
import os
import sys

# Detect if running as packaged executable
is_frozen = getattr(sys, 'frozen', False)

if not is_frozen:
    # Only enable logging when NOT packaged
    BASE_DIR = os.path.expanduser('~/.photo_categorizer_logs')
    os.makedirs(BASE_DIR, exist_ok=True)
    LOG_PATH = os.path.join(BASE_DIR, "app.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - [%(module)s] - %(message)s",
        handlers=[
            logging.StreamHandler(),  # Console log
            logging.FileHandler(LOG_PATH, mode='a')  # File log
        ]
    )
else:
    # Disable all logging when packaged
    logging.disable(logging.CRITICAL)

logger = logging.getLogger("PhotoCategorizer")
