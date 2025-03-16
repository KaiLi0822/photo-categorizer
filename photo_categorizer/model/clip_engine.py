import os
from collections import defaultdict

import torch
from qai_hub_models.models.openai_clip.app import ClipApp
from qai_hub_models.models.openai_clip.model import Clip
from qai_hub_models.utils.asset_loaders import load_image
from photo_categorizer.logger import logger
from photo_categorizer.model.BaseModelEngine import BaseModelEngine
from photo_categorizer.config import FIXED_CATEGORIES, MAX_TOTAL_CATEGORIES, THRESHOLD
import numpy as np
from collections import Counter


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
        self.image_dict = {}

        for filename in os.listdir(image_dir):
            ext = os.path.splitext(filename)[1].lower()
            if ext in [".jpg", ".jpeg", ".png"]:
                image_path = os.path.join(image_dir, filename)
                image_tensor = self.app.process_image(load_image(image_path)).to(self.device)
                self.image_dict[filename] = image_tensor

        logger.info(f"Loaded {len(self.image_dict)} images.")

    def search_images(self, prompt, batch_size=20):
        """
        Search for images matching the text prompt in batches.
        Returns a list of (image_name, similarity_score).
        """
        return self._search_images(prompt, self.image_dict, batch_size)

    def _search_images(self, prompt, image_dict, batch_size=20):
        text_tensor = self.app.process_text(prompt).to(self.device)
        image_items = list(image_dict.items())
        image_tensors = torch.stack([img for _, img in image_items]).squeeze(1)
        image_names = [name for name, _ in image_items]

        results = []
        num_images = image_tensors.shape[0]

        for i in range(0, num_images, batch_size):
            batch_images = image_tensors[i:i + batch_size]
            predictions = self.app.predict_similarity(batch_images, text_tensor).flatten().tolist()
            batch_results = list(zip(image_names[i:i + batch_size], predictions))
            results.extend(batch_results)

        return results

    def _bpe_cluster(self, features, max_clusters):
        """BPE-like clustering with cosine similarity"""
        # Convert to unit vectors for cosine similarity
        if max_clusters == 1:
            return [{"indices": range(len(features)), "mean": features[0]}]
        features = features / np.linalg.norm(features, axis=1, keepdims=True)

        # Initialize each image as its own cluster
        clusters = [{"indices": [i], "mean": features[i]} for i in range(features.shape[0])]

        while len(clusters) > max_clusters:
            # Compute pairwise similarities
            sim_matrix = np.zeros((len(clusters), len(clusters)))
            for i in range(len(clusters)):
                for j in range(i + 1, len(clusters)):
                    sim = clusters[i]["mean"] @ clusters[j]["mean"].T
                    sim_matrix[i, j] = sim

            # Find most similar pair
            i, j = np.unravel_index(np.argmax(sim_matrix), sim_matrix.shape)
            if i > j: i, j = j, i

            # Merge clusters
            merged = {
                "indices": clusters[i]["indices"] + clusters[j]["indices"],
                "mean": (clusters[i]["mean"] * len(clusters[i]["indices"]) +
                         (clusters[j]["mean"] * len(clusters[j]["indices"]))) /
                        (len(clusters[i]["indices"]) + len(clusters[j]["indices"]))
            }

            # Update cluster list
            clusters = [c for idx, c in enumerate(clusters) if idx not in (i, j)] + [merged]

        return clusters

    def auto_categorize_image(self):
        unprocessed_dict = self.image_dict.copy()
        fixed_members = defaultdict(list)
        fixed_names = defaultdict(list)
        for category in FIXED_CATEGORIES:
            members = self._search_images(category, unprocessed_dict)
            fixed_names[category] = [m[0] for m in members if m[1] > THRESHOLD]
            unprocessed_dict = {key: value for key, value in unprocessed_dict.items() if
                                key not in fixed_names[category]}

        remaining_features = []
        remaining_names = list(self.image_dict.keys())
        for k, v in fixed_names.items():
            remaining_names = list(set(remaining_names) - set(v))

        for name in remaining_names:
            remaining_features.append(self.image_dict[name])

        # 3. Calculate remaining cluster allowance
        remaining_clusters = MAX_TOTAL_CATEGORIES - len(FIXED_CATEGORIES)
        if remaining_clusters <= 0:
            print("Warning: Fixed categories already reach maximum allowed")
            remaining_clusters = 1

        # 4. BPE-like clustering for remaining images
        if len(remaining_features) > 0:
            remaining_features = np.vstack(remaining_features)
            clusters = self._bpe_cluster(remaining_features, remaining_clusters)

            # Create cluster names
            cluster_labels = ["other" for i in range(len(clusters))]

            # Assign images to clusters
            for cluster, label in zip(clusters, cluster_labels):
                fixed_names[label] = [remaining_names[i] for i in cluster["indices"]]

        return fixed_names


if __name__ == '__main__':
    clip_engine = ClipEngine()
