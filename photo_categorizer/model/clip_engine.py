# photo_categorizer/clip_engine.py

import os
import numpy as np
import torch
from qai_hub_models.models.openai_clip.app import ClipApp
from qai_hub_models.models.openai_clip.model import MODEL_ASSET_VERSION, MODEL_ID, Clip
from qai_hub_models.utils.asset_loaders import CachedWebModelAsset, load_image
from qai_hub_models.utils.display import display_or_save_image
from photo_categorizer.logger import logger

class ClipEngine:
    def __init__(self):
        """Load CLIP model once."""
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        clip_model = Clip.from_pretrained()
        self.app = ClipApp(clip_model=clip_model)
        self.images = []  # Hold preprocessed image tensors
        self.image_names = []  # Hold image file names
        logger.info(f"[ClipEngine] Model loaded and running on {self.device}")

    def load_images_from_directory(self, image_dir):
        """Preload images into memory for future searches."""
        logger.info(f"[ClipEngine] Loading images from: {image_dir}")

        for filename in os.listdir(image_dir):
            ext = os.path.splitext(filename)[1].lower()
            if ext in [".jpg", ".jpeg", ".png"]:
                image_path = os.path.join(image_dir, filename)
                image_tensor = self.app.process_image(load_image(image_path)).to(self.device)
                self.images.append(image_tensor)
                self.image_names.append(filename)

        logger.info(f"[ClipEngine] Loaded {len(self.images)} images.")

    def search_images(self, image_dir, image_names, text, output_dir=None, display=False):
        """
        Search for images matching the text prompt.
        Returns a list of (image_name, similarity_score).
        """
        text_tensor = self.app.process_text(text).to(self.device)
        images = []
        valid_image_names = []

        for filename in image_names:
            ext = os.path.splitext(filename)[1].lower()
            if ext in [".jpg", ".jpeg", ".png"]:
                image_path = os.path.join(image_dir, filename)
                image_tensor = self.app.process_image(load_image(image_path)).to(self.device)
                images.append(image_tensor)
                valid_image_names.append(filename)

        if not images:
            print("[ClipEngine] No valid images found.")
            return []

        images = torch.stack(images).squeeze(1)
        predictions = self.app.predict_similarity(images, text_tensor).flatten().tolist()
        results = list(zip(valid_image_names, predictions))

        # Display result (optional)
        if display:
            best_match_idx = np.argmax(predictions)
            selected_image_path = os.path.join(image_dir, valid_image_names[best_match_idx])
            most_relevant_image = load_image(selected_image_path)
            display_or_save_image(most_relevant_image, output_dir)

        return results

if __name__ == '__main__':
    clip_engine = ClipEngine()
