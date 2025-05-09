
# 📂 Photo Categorizer App

Photo Categorizer is a desktop application that allows you to **automatically categorize images into different folders** based on prompts using the CLIP model. The application includes a **PyQt6 frontend GUI**, a **Flask backend**, and a **model module based on OpenAI CLIP**.

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
│   ├── model/              # Model definitions and factory
│   │   ├── BaseModelEngine.py
│   │   ├── clip_engine.py
│   │   ├── model_factory.py
│   │   └── model_types.py
│   ├── config.py           # configuration
│   ├── logger.py           # Logging configuration
│   ├── main.py             # Application entry point
│   └── state.py            # State management
├── sample_pictures/
└── README.md
```

---

## 🛠️ Project Setup with Poetry

This project uses [Poetry](https://python-poetry.org/) to manage dependencies and environments.

### Step 1: Install Poetry

Follow the official installation guide here: https://python-poetry.org/docs/#installation

Or install directly via the terminal:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

> After installation, restart your terminal or run:
>
> ```bash
> source $HOME/.poetry/env
> ```

### Step 2: Clone the Repository

```bash
git clone https://github.com/KaiLi0822/photo-categorizer.git
cd photo-categorizer
```

### Step 3: Install Dependencies

```bash
poetry install
```

### Step 4: Activate the Virtual Environment

```bash
poetry shell
```

### Step 5: Run the Application

```bash
python photo_categorizer/main.py
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
  - Specify **output folders** and **text prompts** for further categorization.
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
  - `/auto-categorize`: Automatically categorize images into predefined categories.

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
- Windows
  - Package the backend as an executable file

    ```bash
    pyinstaller --onefile --name backend_executable --hidden-import ftfy --hidden-import regex --add-data "path\\to\\qai_hub_models\\asset_bases.yaml:qai_hub_models" photo_categorizer\\backend\\backend.py
    ```

  - Test the backend independently

    ```bash
    .\backend_executable
    ```
    
  - Package the app

    ```bash
    pyinstaller --windowed --onefile --name PhotoCategorizer --add-binary "dist\\backend_executable.exe;backend_executable" photo_categorizer\\main.py
    ```
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
    
  - Package the app

    ```bash
    pyinstaller --windowed --onefile --name PhotoCategorizer \
    --add-binary "dist/backend_executable:backend_executable" \
    photo_categorizer/main.py
    ```

---

## ✅ Usage

1. **Select the target folder** — Browse and choose the folder containing images you want to categorize.
2. **Choose a category for further categorization** — Pick one of the predefined categories (e.g., pets, people, food, landscape, other).
3. **Add output folders and prompts** — Define folder names and prompts that the AI model will use to classify images.
4. **Start categorization** — Click the Start button to initiate the process. You can track the status of each folder as it's being processed.
5. **Review results** — After processing, images will be copied into corresponding output folders based on the prompts and categories.

---

## 🖥️ Proposed UI
![Proposed_UI](./UI_image.jpg)

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

