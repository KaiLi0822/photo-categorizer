import logging

# =============================
# Global Logging configuration
# =============================
logging.basicConfig(
    level=logging.INFO,  # Use DEBUG for more detailed logs if needed
    format="%(asctime)s - %(levelname)s - [%(module)s] - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Log to console
        logging.FileHandler("app.log", mode='a')  # Optional: Log to file
    ]
)

# Get a logger instance
logger = logging.getLogger("PhotoCategorizer")

