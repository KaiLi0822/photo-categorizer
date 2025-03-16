from enum import Enum

class StateTypes(Enum):
    START = "Start"
    BACKEND_LOADING = "Backend Loading"
    BACKEND_LOADED = "Backend Loaded"
    MODEL_LOADING = "Model Loading"
    MODEL_LOADED = "Model Loaded"

    FIRST_CATEGORIZING = "First Categorizing"
    FIRST_CATEGORIZED = "First Categorized"

    SECOND_IMAGES_LOADED = "Second Images Loaded"
    SECOND_IMAGES_LOADING = "Second Images Loading"
    SECOND_CATEGORIZING = "Second Categorizing"
    SECOND_CATEGORIZED = "Second Categorized"

