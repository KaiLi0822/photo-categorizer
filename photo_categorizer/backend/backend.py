from flask import Flask, request, jsonify
import os
import shutil
from photo_categorizer.logger import logger
import threading
from photo_categorizer.model.model_factory import ModelFactory
from photo_categorizer.state import StateTypes
from photo_categorizer.model.BaseModelEngine import BaseModelEngine
from photo_categorizer.config import BACKEND_PORT, BACKEND_HOST, THRESHOLD, FIXED_CATEGORIES
app = Flask(__name__)

model: BaseModelEngine = None  # Lazy initialization

# Dictionary to store status of each folder being processed
processing_status = {}


# ----------------- Load Model -----------------
@app.route('/load-model', methods=['POST'])
def load_model():
    """API to load model."""
    data = request.json
    model_name = data.get('model')
    logger.info("Received request to load model.")
    # Start model loading in a separate thread
    threading.Thread(target=load_model_async, args=(model_name,), daemon=True).start()
    return jsonify({"message": "Model loading started in background."})


def load_model_async(model_name: str):
    """Run model loading in a separate thread to avoid blocking requests."""
    global model
    try:
        if model is None:
            model = ModelFactory.get_model(model_name)
        logger.info(f"Model successfully loaded: {model_name}")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")


@app.route('/model-status', methods=['GET'])
def model_status():
    """API to get model loading status."""
    global model
    if model is None:
        return jsonify({"status": StateTypes.MODEL_LOADING.value})
    else:
        return jsonify({"status": StateTypes.MODEL_LOADED.value})


# ----------------- Load Images -----------------
@app.route('/load-images', methods=['POST'])
def load_images():
    """API to trigger image loading without blocking."""
    global model
    if model is None:
        return jsonify({"error": "Model is not loaded. Please load the model first."}), 400

    data = request.json
    target_folder = data.get('target_folder')

    if not target_folder or not os.path.isdir(target_folder):
        return jsonify({"error": "Invalid target folder."}), 400

    # Start image loading
    model.load_images_from_directory(target_folder)
    return jsonify({"message": "Images loaded."})


# ----------------- Start Processing -----------------
@app.route('/start-process', methods=['POST'])
def start_process():
    """API to start processing one output folder with a given prompt."""
    global model
    if model is None:
        return jsonify({"error": "Model is not loaded. Please load the model first."}), 400

    data = request.json
    target_folder = data.get('target_folder')
    output = data.get('output')
    selected_text = data.get('selected_text')

    if not target_folder or not os.path.isdir(target_folder):
        return jsonify({"error": "Invalid target folder."}), 400
    if not output or 'folder_name' not in output or 'prompt' not in output:
        return jsonify({"error": "Invalid output data."}), 400

    folder_name = output['folder_name']
    prompt = output['prompt']
    selected_text_folder_name = selected_text + "_" + folder_name

    # Set status to "processing"
    processing_status[selected_text_folder_name] = "processing"
    logger.info(f"Started processing for {selected_text_folder_name} with prompt: {prompt}")

    # Start actual processing in a separate thread
    threading.Thread(
        target=process_images_async,
        args=(target_folder, selected_text, folder_name, prompt),
        daemon=True
    ).start()

    return jsonify({"message": f"Processing started for {folder_name}."})


def process_images_async(target_folder, selected_text, output_folder, prompt):
    """Process images and move matches to output folder."""
    global model, processing_status
    selected_text_folder_name = selected_text + "_" + output_folder
    try:
        selected_text_folder_name = selected_text + "_" + output_folder
        output_path = os.path.join(target_folder, selected_text, output_folder)
        os.makedirs(output_path, exist_ok=True)

        # Search images based on prompt
        logger.info(f"Running search for prompt '{prompt}' into '{output_path}'")
        results = model.search_images(
            prompt=prompt
        )

        model.load_images_from_directory(target_folder)
        logger.info(f"Loading images from '{target_folder}'")
        # Copy matching images (customize this logic as needed)
        for image_name, score in results:
            if score > THRESHOLD:
                src = os.path.join(target_folder, selected_text, image_name)
                dst = os.path.join(output_path, image_name)
                shutil.copy(src, dst)
                logger.info(f"Copied {image_name} with score {score}")

        # Mark processing as completed
        processing_status[selected_text_folder_name] = "completed"
        logger.info(f"Completed processing for {output_folder}")

    except Exception as e:
        logger.error(f"Failed to process {output_folder}: {e}")
        processing_status[selected_text_folder_name] = "error"

    finally:
        model.clean_memory()
        logger.info(f"loaded image for {target_folder} cleaned")


@app.route('/auto-categorize', methods=['POST'])
def auto_categorize():
    """API to start processing one output folder with a given prompt."""
    global model
    if model is None:
        return jsonify({"error": "Model is not loaded. Please load the model first."}), 400


    data = request.json
    target_folder = data.get('target_folder')

    if not target_folder or not os.path.isdir(target_folder):
        return jsonify({"error": "Invalid target folder."}), 400

    model.load_images_from_directory(target_folder)

    processing_status["auto"] = "processing"
    logger.info(f"Started processing for auto categorizer")

    # Start actual processing in a separate thread
    threading.Thread(
        target=auto_categorize_async,
        args=(target_folder,),
        daemon=True
    ).start()

    return jsonify({"message": f"Processing started for auto categorizer."})


def auto_categorize_async(target_folder):
    """Process images and move matches to output folder."""
    global model, processing_status
    try:
        for output_folder in FIXED_CATEGORIES + ["other"]:
            output_path = os.path.join(target_folder, output_folder)
            os.makedirs(output_path, exist_ok=True)

        # Search images based on prompt
        logger.info(f"Running auto categorizer for {target_folder}")
        results = model.auto_categorize_image()


        # Copy matching images (customize this logic as needed)

        for k, v in results.items():
            for image_name in v:
                src = os.path.join(target_folder, image_name)
                dst = os.path.join(os.path.join(target_folder, str(k)), image_name)
                shutil.copy(src, dst)

        # Mark processing as completed
        processing_status["auto"] = "completed"
        logger.info(f"Completed processing for {target_folder}")

    except Exception as e:
        logger.error(f"Failed to process {target_folder}: {e}")
        processing_status["auto"] = "error"

    finally:
        model.clean_memory()
        logger.info(f"loaded image for auto categorizer cleaned")

# ----------------- Processing Status -----------------
@app.route('/process-status', methods=['GET'])
def process_status():
    """API to check processing status for a specific folder."""
    folder_name = request.args.get('folder')
    if not folder_name:
        return jsonify({"error": "Folder name is required."}), 400

    status = processing_status.get(folder_name, "not_started")
    logger.info(f"Status check for {folder_name}: {status}")
    return jsonify({"status": status})




# ----------------- Run App -----------------
if __name__ == '__main__':
    logger.info(f"Starting backend on {BACKEND_HOST}:{BACKEND_PORT}...")
    logger.info("Initializing Flask backend...")
    app.run(debug=False, host=BACKEND_HOST, port=BACKEND_PORT)
