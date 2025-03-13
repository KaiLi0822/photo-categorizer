import os
import sys
import subprocess
import requests
import socket
import platform

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton,
    QFileDialog, QLineEdit, QMessageBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QTimer
from photo_categorizer.logger import logger
from photo_categorizer.model.model_types import ModelTypes
from photo_categorizer.state import StateTypes
from PyQt6.QtWidgets import QProgressBar
from photo_categorizer.config import BASE_URL, BACKEND_PORT, BACKEND_HOST

QSS_STYLE = """
QWidget {
    font-size: 14px;
}

QLineEdit {
    padding: 8px;
    border: 1px solid gray;
    border-radius: 5px;
}

QPushButton {
    padding: 8px;
    background-color: #0078D7;
    color: white;
    border-radius: 5px;
}

QPushButton:hover {
    background-color: #005BB5;
}
"""
class PhotoCategorizerApp(QWidget):
    def __init__(self):
        super().__init__()
        # GUI setup
        self.setStyleSheet(QSS_STYLE)
        self.setWindowTitle("Photo Categorizer")
        self.setGeometry(200, 200, 800, 600)
        self.output_fields = []
        self.build_ui()
        self.state = StateTypes.START

        # Backend and model are now deferred — GUI will show first
        QTimer.singleShot(100, self.start_backend)
        QApplication.instance().aboutToQuit.connect(self.cleanup_backend)

    # ---------------------- Backend Management ----------------------

    def start_backend(self):

        """Start Flask backend and ensure it's ready."""

        if getattr(sys, 'frozen', False):
            # Packaged mode
            backend_path = self.resource_path(os.path.join('backend_executable', 'backend_executable.exe') if platform.system() == 'Windows' else 'backend_executable/backend_executable')
        else:
            # Development mode
            backend_path = self.resource_path(os.path.join('backend', 'backend.py'))

        # Windows-specific creation flag
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if platform.system() == 'Windows' else 0

        self.backend_process = subprocess.Popen(
            [sys.executable, backend_path] if backend_path.endswith('.py') else [backend_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=creationflags  # Important on Windows
        )

        QTimer.singleShot(500, lambda: self.check_backend_ready())  # Check soon

    def check_backend_ready(self):
        """Check if backend is ready without blocking."""
        logger.info("Checking backend readiness...")
        try:
            response = requests.get(f"{BASE_URL}")
            if response.status_code in (200, 404):
                logger.info("Backend is ready!")
                self.switchState(StateTypes.BACKEND_LOADED)
                self.load_mode()
            else:
                logger.warning("Backend not ready, retrying...")
                self.switchState(StateTypes.BACKEND_LOADING)
                QTimer.singleShot(1000, self.check_backend_ready)  # Retry
        except requests.ConnectionError:
            logger.warning("Backend connection failed, retrying...")
            self.switchState(StateTypes.BACKEND_LOADING)
            QTimer.singleShot(1000, self.check_backend_ready)  # Retry again

    def cleanup_backend(self):
        """Gracefully terminate backend on app exit and ensure port is freed."""
        if self.backend_process:
            logger.info("Shutting down backend...")
            self.backend_process.terminate()
            try:
                self.backend_process.wait(timeout=5)
                logger.info("Backend process terminated.")
            except subprocess.TimeoutExpired:
                logger.warning("Force killing backend...")
                self.backend_process.kill()

            # Final check: Is port 5050 still occupied?
            if self.is_port_in_use(BACKEND_PORT):
                logger.error(f"Port {BACKEND_PORT} is still in use. Backend may not have shut down properly.")
            else:
                logger.info(f"Backend successfully shut down. Port {BACKEND_PORT} is free.")

    def is_port_in_use(self, port):
        """Check if a port is in use."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex((BACKEND_HOST, port)) == 0

    # ---------------------- Model Initialization ----------------------

    def load_mode(self):
         # Call backend to load images
        try:
            response = requests.post(f"{BASE_URL}load-model", json={"model": ModelTypes.CLIP.value})
            if response.status_code == 200:
                self.switchState(StateTypes.MODEL_LOADING)
                logger.info(f"Backend response: {response.json().get('message')}")
                self.start_polling_model_status()
            else:
                error_msg = response.json().get('error', 'Unknown error')
                logger.error(f"Backend error: {error_msg}")
        except Exception as e:
            logger.error(f"Connection error: {e}")

    def start_polling_model_status(self):
        """Start polling backend for model status every 2 seconds."""
        self.model_status_timer = QTimer(self)
        self.model_status_timer.timeout.connect(self.check_model_status)
        self.model_status_timer.start(2000)  # Poll every 2 seconds

    def check_model_status(self):
        """Check if model is loaded and update status bar."""
        try:
            response = requests.get(f"{BASE_URL}/model-status")
            if response.status_code == 200:
                status = response.json().get("status")
                if status == StateTypes.MODEL_LOADED.value:
                    self.switchState(StateTypes.MODEL_LOADED)
                    self.model_status_timer.stop()  # Stop polling
            else:
                logger.error("Error checking model status.")
        except Exception as e:
            logger.error(f"Failed to check model status: {e}")

    # ---------------------- GUI Layout and Logic ----------------------

    def build_ui(self):
        """Build the main GUI layout."""
        layout = QVBoxLayout(self)

        # Target folder selection
        target_layout = QHBoxLayout()
        self.target_entry = QLineEdit()
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.select_folder)
        target_layout.addWidget(QLabel("Target Folder:"))
        target_layout.addWidget(self.target_entry)
        target_layout.addWidget(browse_button)
        layout.addLayout(target_layout)

        # Scroll area for dynamic filters
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; }")
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)  # No margins
        self.scroll_layout.setSpacing(5)  # Small gap between rows
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area)

        # Initial filter input
        self.add_output_input()

        # Control buttons
        add_button = QPushButton("Add Folder")
        add_button.clicked.connect(self.add_output_input)
        layout.addWidget(add_button)

        start_button = QPushButton("Start Categorization")
        start_button.clicked.connect(self.start_categorization)
        layout.addWidget(start_button)

        # Status bar
        self.state_label = QLabel()
        layout.addWidget(self.state_label)

    def resource_path(self, relative_path):
        """Get absolute path to resource, works for dev and PyInstaller."""
        base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
        return os.path.join(base_path, relative_path)

    def select_folder(self):
        """Select the target folder and notify backend to load images."""
        if self.state == StateTypes.IMAGES_LOADING:
            QMessageBox.warning(self, "Warning", "Loading images...")
            return
        folder = QFileDialog.getExistingDirectory(self, "Select Target Directory")
        if folder:
            self.target_entry.setText(folder)
            logger.info(f"Selected folder: {folder}")
            # Start polling model status before loading images
            self.start_loading_images()

    def start_loading_images(self):
        """Start polling backend for model status every 2 seconds until ready to load images."""
        if hasattr(self, 'status_check_timer') and self.status_check_timer.isActive():
            self.status_check_timer.stop()
            self.status_check_timer.deleteLater()  # Clean up the old timer
        self.status_check_timer = QTimer(self)
        self.status_check_timer.timeout.connect(self.check_status_and_load_images)
        self.status_check_timer.start(2000)  # Poll every 2 seconds

    def check_status_and_load_images(self):
        """Check if model is loaded and trigger image loading if ready."""
        try:
            if self.state == StateTypes.MODEL_LOADED or self.state == StateTypes.IMAGES_LOADED:
                self.status_check_timer.stop()  # Stop polling
                self.switchState(StateTypes.IMAGES_LOADING)
                self.load_images(self.target_entry.text().strip())  # Trigger image load
            else:
                logger.info("State: Model is loading or previous images are loading.")
        except Exception as e:
            logger.error(f"Failed to check state: {e}")

    def load_images(self, folder):
        """Send a request to backend to load images from selected folder."""
        logger.info(f"Sending load-images request for folder: {folder}")
        try:
            response = requests.post(f"{BASE_URL}/load-images", json={"target_folder": folder})
            if response.status_code == 200:
                message = response.json().get('message', "Images loaded.")
                logger.info(f"Backend response: {message}")
                self.switchState(StateTypes.IMAGES_LOADED)
            else:
                error_msg = response.json().get('error', 'Unknown error')
                logger.error(f"Backend error: {error_msg}")
        except Exception as e:
            logger.error(f"Connection error: {e}")

    def add_output_input(self):
        """Add a new row for folder name and prompt."""
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.NoFrame)
        frame_layout = QHBoxLayout(frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)  # No margins
        frame_layout.setSpacing(10)  # Small gap between widgets
        frame_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Input fields
        folder_name_input = QLineEdit()
        folder_name_input.setPlaceholderText("Folder Name")
        folder_name_input.setFixedWidth(150)  # Short width

        prompt_input = QLineEdit()
        prompt_input.setPlaceholderText("Prompt")
        prompt_input.setMinimumWidth(250)  # Longer width

        # Labels with fixed width for alignment
        label_folder = QLabel("Output Folder:")
        label_folder.setFixedWidth(90)
        label_prompt = QLabel("Prompt:")
        label_prompt.setFixedWidth(50)

        # Delete button
        delete_button = QPushButton("Delete")
        delete_button.setFixedWidth(70)
        delete_button.clicked.connect(lambda: self.delete_output_input(frame))

        # Add all widgets to frame layout
        frame_layout.addWidget(label_folder)
        frame_layout.addWidget(folder_name_input)
        frame_layout.addWidget(label_prompt)
        frame_layout.addWidget(prompt_input)
        frame_layout.addWidget(delete_button)

        # Add to scrollable area
        self.scroll_layout.addWidget(frame)
        self.output_fields.append((folder_name_input, prompt_input, frame))

    def delete_output_input(self, frame):
        """Remove a filter row."""
        for i, (_, _, frm) in enumerate(self.output_fields):
            if frm == frame:
                self.output_fields.pop(i)
                break
        self.scroll_layout.removeWidget(frame)
        frame.deleteLater()

    # ---------------------- Categorization Logic ----------------------
    def start_categorization(self):
        """Start categorization process with progress tracking for each output folder."""

        # Step 1: Check if images are loaded
        if not self.target_entry.text().strip():
            QMessageBox.warning(self, "Warning", "Please select a target folder.")
            return

        if self.state != StateTypes.IMAGES_LOADED:
            QMessageBox.warning(self, "Warning", "Images are not loaded yet. Please try again later.")
            return

        # Step 2: Collect folders/prompts
        self.outputs = [
            {"folder_name": fn.text().strip(), "prompt": pr.text().strip()}
            for fn, pr, _ in self.output_fields if fn.text().strip() and pr.text().strip()
        ]
        if not self.outputs:
            QMessageBox.warning(self, "Warning", "Please add at least one output folder and prompt.")
            return

        # Step 3: Setup progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, len(self.outputs))  # Total output folders
        self.progress_bar.setValue(0)
        self.layout().addWidget(self.progress_bar)

        # Step 4: Initialize index and start first job
        self.current_output_index = 0
        self.process_next_output()

    def process_next_output(self):
        """Process the next output folder in the list."""
        if self.current_output_index >= len(self.outputs):
            # Step 5: All done
            self.finish_categorization()
            return

        output = self.outputs[self.current_output_index]
        logger.info(f"Starting processing for: {output['folder_name']}")
        self.state_label.setText(f"Processing folder: {output['folder_name']}")

        # Step 4.1: Trigger the job
        try:
            response = requests.post(f"{BASE_URL}start-process", json={
                "target_folder": self.target_entry.text().strip(),
                "output": output
            })
            if response.status_code == 200:
                logger.info(f"Triggered backend processing for {output['folder_name']}")
                # Step 4.2: Start polling for status
                self.poll_processing_status(output['folder_name'])
            else:
                error_msg = response.json().get('error', 'Unknown error')
                logger.error(f"Failed to start processing: {error_msg}")
                self.move_to_next_output()

        except Exception as e:
            logger.error(f"Failed to trigger processing: {e}")
            self.move_to_next_output()

    def poll_processing_status(self, folder_name):
        """Poll backend to check if processing is complete."""
        logger.info(f"Polling status for {folder_name}")

        def check_status():
            try:
                response = requests.get(f"{BASE_URL}process-status?folder={folder_name}")
                if response.status_code == 200:
                    status = response.json().get('status')
                    logger.info(f"Status for {folder_name}: {status}")

                    if status == "completed":
                        # Step 4.3: Move to next output
                        self.progress_bar.setValue(self.current_output_index + 1)
                        self.move_to_next_output()

                    elif status == "error":
                        self.progress_bar.setValue(self.current_output_index + 1)
                        self.move_to_next_output()
                        logger.error(self, "Error", f"Error in {folder_name}: {response.json().get('error')}")

                    else:
                        # Still processing — poll again
                        QTimer.singleShot(2000, check_status)

                else:
                    logger.error(f"Failed to check status for {folder_name}")
                    self.move_to_next_output()

            except Exception as e:
                logger.error(f"Error while polling {folder_name}: {e}")
                QTimer.singleShot(2000, check_status)  # Retry

        # Start first check
        QTimer.singleShot(2000, check_status)

    def move_to_next_output(self):
        """Move to next output folder after current one is done."""
        self.current_output_index += 1
        self.process_next_output()

    def finish_categorization(self):
        """Handle finishing of all outputs."""

        self.switchState(StateTypes.CATEGORIZED)

        # Optional: Ask to open folder
        choice = QMessageBox.question(self, "Open Folder", "Open target folder now?",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if choice == QMessageBox.StandardButton.Yes:
            # Cross-platform way to open folder
            folder_path = self.target_entry.text().strip()
            system_platform = platform.system()

            if system_platform == "Windows":
                os.system(f'explorer "{folder_path}"')
            elif system_platform == "Darwin":  # macOS
                os.system(f'open "{folder_path}"')
            else:  # Linux and others
                os.system(f'xdg-open "{folder_path}"')

        # Step 5: Reset interface
        self.layout().removeWidget(self.progress_bar)
        self.progress_bar.deleteLater()
        self.progress_bar = None

        self.target_entry.clear()
        for _, _, frame in self.output_fields:
            frame.deleteLater()
        self.output_fields.clear()
        self.add_output_input()
        self.switchState(StateTypes.MODEL_LOADED)

    def switchState(self, state: StateTypes):
        self.state = state
        self.state_label.setText(state.value)


# ---------------------- Main App Runner ----------------------

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PhotoCategorizerApp()
    window.show()
    sys.exit(app.exec())
