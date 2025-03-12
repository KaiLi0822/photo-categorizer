
# 📂 Photo Categorizer App

Photo Categorizer is a desktop application that allows you to **automatically categorize images into different folders** based on prompts using the CLIP model. The application includes a **PyQt6 frontend GUI**, a **Flask backend**, and a **model service based on OpenAI CLIP**.

---

## 🏗️ Project Structure

```
photo-categorizer/
│
├── photo_categorizer/
│   ├── backend/            # Flask backend service
│   │   └── backend.py
│   ├── frontend/           # PyQt6 GUI frontend
│   │   ├── frontend.py
│   │   └── styles.qss      # Styling
│   ├── model/              # Model definitions and factory
│   │   ├── BaseModelEngine.py
│   │   ├── clip_engine.py
│   │   ├── model_factory.py
│   │   └── model_types.py
│   ├── config.py           # configuration
│   ├── logger.py           # Logging configuration
│   ├── main.py             # Application entry point
│   └── state.py            # State management
└── README.md
```

---

## 🚀 Features

- **Categorize images** using natural language prompts (via CLIP model).
- **Modern PyQt6 GUI** for selecting target folder and prompts.
- Real-time **progress bar** tracking categorization process.
- Backend status monitoring (model load, image load, per-folder process).
- Asynchronous **threading** for backend model/image processing without blocking UI.
- **Backend state polling** to sync frontend.
- Easy packaging for distribution (`PyInstaller` ready).

---

## 🔧 How It Works

### 1. **Frontend (PyQt6)**
- Provides a simple GUI where users can:
  - Select a **target folder** containing images.
  - Specify **output folders** and **text prompts** for categorization.
- Starts backend service automatically.
- Monitors backend status and updates UI accordingly.
- Initiates image loading and categorization when ready.
- Progress bar updates as each folder gets processed.
- Option to open the categorized folder when done.

> **Frontend file**: `photo_categorizer/frontend/frontend.py`

---

### 2. **Backend (Flask)**
- Handles communication between frontend and model.
- Supports API endpoints:
  - `/load-model`: Load the selected model in background.
  - `/model-status`: Check if model is loaded.
  - `/load-images`: Preload and process images from a target directory.
  - `/start-process`: Start image classification per output folder/prompt.
  - `/process-status`: Track the status of each folder being processed.

> **Backend file**: `photo_categorizer/backend/backend.py`

---

### 3. **Model (CLIP)**
- Loads CLIP model to run similarity searches on images.
- Processes images to prepare them for similarity comparison.
- Searches for image similarities to user-provided prompts.
- Supports efficient batch similarity search.

> **Model file**: `photo_categorizer/model/clip_engine.py`

---

## 🖥️ How to Run

### 1. **Install Requirements**

  ```bash
  poetry install
  ```

### 2. **Run the Application**

  ```bash
  python photo_categorizer/main.py
  ```

### 3. **Optional: Package the App**

Using PyInstaller:

- Mac
  - Package the backend as an executable file

    ```bash
    pyinstaller --onefile --name backend_executable \
    --hidden-import ftfy --hidden-import regex \
    --add-data "/path/to/qai_hub_models/asset_bases.yaml:qai_hub_models" \
    photo_categorizer/backend/backend.py
    ```

  - Test the backend independently

    ```bash
    chmod +x ./backend_executable
    ./backend_executable
    ```
    
  - Change the code(Line 62 - 80 in frontend.py)

    Inside frontend.py, adjust the backend launching logic depending on whether you are running locally for development or as a packaged app:
    
    ```python
    # --- Run backend in local development mode (using Python script) ---
    # This is used when running the app locally (e.g., during development in IDE).
    backend_path = self.resource_path(os.path.join('backend', 'backend.py'))
    backend_process = subprocess.Popen(
        [sys.executable, backend_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # --- Run backend in packaged app mode (using compiled executable) ---
    # Uncomment this block when running the packaged application.
    # Ensure that the backend executable has proper permissions to run.
    # backend_path = self.resource_path('backend_executable/backend_executable')  # Path to backend executable
    # os.chmod(backend_path, 0o755)  # Ensure executable permission (rwxr-xr-x)
    # backend_process = subprocess.Popen(
    #     [backend_path],
    #     stdout=subprocess.PIPE,
    #     stderr=subprocess.PIPE
    # )
    ```
    
  - Package the app

    ```bash
    pyinstaller --windowed --onefile --name PhotoCategorizer \
    --add-binary "dist/backend_executable:backend_executable" \
    photo_categorizer/main.py
    ```

---

## ✅ Usage

1. **Select target folder** — choose the images to categorize.
2. **Add output folders and prompts** — specify how you want to categorize images.
3. **Start categorization** — watch the progress bar as each folder is processed.
4. **Review results** — categorized images will be moved into the corresponding output folders.

---



## 📷 Screenshots

### Main Interface
![Main Interface](./image.jpg)



---

## 📦 Future Improvements

- [ ] Add image preview.
- [ ] Add drag-and-drop for target folder.
- [ ] Extend model choices (support BLIP, LLaVA, etc.).
- [ ] Threshold slider in UI.

---

## 👨‍💻 Authors

- KeeHLY
  - li.kai4@northeastern.edu
  - liu.muz@northeastern.edu
  - li.xueyun@northeastern.edu
  - cheng.yao1@northeastern.edu
  - liu.zile@northeastern.edu

---

## 📜 License

This project is licensed under the [MIT License](./LICENSE).

