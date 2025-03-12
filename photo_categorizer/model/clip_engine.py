import os
import torch
from qai_hub_models.models.openai_clip.app import ClipApp
from qai_hub_models.models.openai_clip.model import Clip
from qai_hub_models.utils.asset_loaders import load_image
from photo_categorizer.logger import logger
from photo_categorizer.model.BaseModelEngine import BaseModelEngine


class ClipEngine(BaseModelEngine):
    def __init__(self):
        super().__init__()  # Initialize BaseModelEngine attributes
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.app = None
        self.load_model()

    def load_model(self):
        """Load CLIP model."""
        clip_model = Clip.from_pretrained()
        self.app = ClipApp(clip_model=clip_model)
        logger.info(f"Model loaded and running on {self.device}")

    def load_images_from_directory(self, image_dir):
        """Preload images into memory for future searches."""
        logger.info(f"Loading images from: {image_dir}")
        self.images = []
        self.image_names = []

        for filename in os.listdir(image_dir):
            ext = os.path.splitext(filename)[1].lower()
            if ext in [".jpg", ".jpeg", ".png"]:
                image_path = os.path.join(image_dir, filename)
                image_tensor = self.app.process_image(load_image(image_path)).to(self.device)
                self.images.append(image_tensor)
                self.image_names.append(filename)

        logger.info(f"Loaded {len(self.images)} images.")

    def search_images(self, prompt):
        """
        Search for images matching the text prompt.
        Returns a list of (image_name, similarity_score).
        """
        text_tensor = self.app.process_text(prompt).to(self.device)
        images = torch.stack(self.images).squeeze(1)
        predictions = self.app.predict_similarity(images, text_tensor).flatten().tolist()
        results = list(zip(self.image_names, predictions))
        return results


if __name__ == '__main__':
    clip_engine = ClipEngine()
