from flask import Flask, request, jsonify
import os
import shutil
from photo_categorizer.logger import logger
from photo_categorizer.model.clip_engine import ClipEngine

app = Flask(__name__)
clip_engine = ClipEngine()

@app.route('/categorize', methods=['POST'])
def categorize():
    data = request.json
    target_folder = data['target_folder']
    outputs = data['outputs']
    logger.info(f"Received categorization request: {data}")

    if not os.path.isdir(target_folder):
        return jsonify({"error": "Invalid target folder."}), 400

    image_files = [f for f in os.listdir(target_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    for output in outputs:
        folder_name = output['folder_name']
        prompt = output['prompt']
        output_path = os.path.join(target_folder, folder_name)
        os.makedirs(output_path, exist_ok=True)

        for image_file in image_files:
            image_path = os.path.join(target_folder, image_file)
            if filter_images_by_prompt(image_path, prompt):
                shutil.copy(image_path, output_path)

    return jsonify({"message": "Categorization done successfully!"})

@app.route('/load-images', methods=['POST'])
def load_images():
    """API to load images from a folder into memory."""
    data = request.json
    target_folder = data.get('target_folder')

    if not target_folder or not os.path.isdir(target_folder):
        return jsonify({"error": "Invalid target folder."}), 400

    clip_engine.load_images_from_directory(target_folder)
    return jsonify({"message": f"Loaded {len(clip_engine.images)} images from {target_folder}."})

if __name__ == '__main__':
    app.run(debug=False, host="127.0.0.1", port=5050)
