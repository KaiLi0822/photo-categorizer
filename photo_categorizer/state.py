from enum import Enum

class StateTypes(Enum):
    START = "Start"
    BACKEND_LOADING = "Backend Loading"
    BACKEND_LOADED = "Backend Loaded"
    MODEL_LOADING = "Model Loading"
    MODEL_LOADED = "Model Loaded"
    IMAGES_LOADED = "Images Loaded"
    CATEGORIZING = "Categorizing"
    CATEGORIZED = "Categorized"

