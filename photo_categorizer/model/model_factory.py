from photo_categorizer.model.model_types import ModelTypes
from photo_categorizer.model.clip_engine import ClipEngine
from photo_categorizer.logger import logger

class ModelFactory:
    _instances = {}  # Cache to hold singleton instances of models

    @staticmethod
    def get_model(model_type: str):
        """
        Load model based on model_type Enum.
        Return a singleton instance if already loaded.
        """
        if model_type in ModelFactory._instances:
            logger.info(f"Reusing existing instance for {model_type}")
            return ModelFactory._instances[model_type]

        logger.info(f"Loading model: {model_type}")

        if model_type == ModelTypes.CLIP.value:
            model = ClipEngine()
        else:
            raise ValueError(f"Unsupported model type: {model_type}")

        # Cache the instance
        ModelFactory._instances[model_type] = model
        logger.info(f"Model {model_type} loaded successfully and cached.")
        return model
