# photo_categorizer/model/base_model_engine.py

from abc import ABC, abstractmethod

class BaseModelEngine(ABC):
    """
    Abstract Base Class for all Model Engines.
    """

    def __init__(self):
        self.device = None
        self.images = []  # Hold preprocessed image tensors
        self.image_names = []  # Hold image file names

    @abstractmethod
    def load_model(self):
        """Load the model. Must be implemented by subclass."""
        pass

    @abstractmethod
    def load_images_from_directory(self, image_dir):
        """Preload images from directory. Must be implemented by subclass."""
        pass

    @abstractmethod
    def search_images(self, prompt, batch_size):
        pass

    @abstractmethod
    def auto_categorize_image(self):
        pass

    # @abstractmethod
    # def search_images(self, image_dir, image_names, text, output_dir=None, display=False):
    #     """Search images by text. Must be implemented by subclass."""
    #     pass
