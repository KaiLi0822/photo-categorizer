from flask import Flask, request, jsonify
import os
import shutil
from photo_categorizer.model.model import filter_images_by_prompt

app = Flask(__name__)

@app.route('/categorize', methods=['POST'])
def categorize():
    data = request.json
    target_folder = data['target_folder']
    outputs = data['outputs']

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

if __name__ == '__main__':
    app.run(debug=True)
