import os
import sys
import time
import subprocess
import requests
import atexit
import socket

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton,
    QFileDialog, QLineEdit, QMessageBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QTimer
from photo_categorizer.logger import logger
from photo_categorizer.model.model_types import ModelTypes
from photo_categorizer.state import StateTypes
from PyQt6.QtWidgets import QProgressBar



class PhotoCategorizerApp(QWidget):
    def __init__(self):
        super().__init__()
        # GUI setup
        self.setStyleSheet(self.load_stylesheet())
        self.setWindowTitle("Photo Categorizer")
        self.setGeometry(200, 200, 800, 600)
        self.output_fields = []
        self.build_ui()
        self.status = StateTypes.START

        # Backend initialization
        self.backend_process = self.start_backend()

        # Model initialization
        self.load_mode()





    # ---------------------- Backend Management ----------------------

    def start_backend(self):
        """Start Flask backend and ensure it's ready."""
        backend_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', 'backend', 'backend.py')
        )
        backend_process = subprocess.Popen(
            [sys.executable, backend_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        atexit.register(self.cleanup_backend, backend_process)

        if not self.wait_for_backend():
            logger.error("Failed to start backend. Please check backend.py")
            sys.exit(1)

        return backend_process

    def wait_for_backend(self, url='http://127.0.0.1:5050/', timeout=10):
        """Wait until backend is ready to accept requests."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url)
                if response.status_code in (200, 404):  # 404 is acceptable (if root route isn't defined)
                    self.status = StateTypes.BACKEND_LOADED
                    logger.info("Backend is up and running!")
                    return True
            except requests.ConnectionError:
                pass
            time.sleep(1)
        logger.info("Backend failed to start in time.")
        return False

    def cleanup_backend(self, backend_process):
        """Gracefully terminate backend on app exit and ensure port is freed."""
        if backend_process:
            logger.info("Shutting down backend...")
            backend_process.terminate()
            try:
                backend_process.wait(timeout=5)
                logger.info("Backend process terminated.")
            except subprocess.TimeoutExpired:
                logger.warning("Force killing backend...")
                backend_process.kill()

            # Final check: Is port 5050 still occupied?
            if self.is_port_in_use(5050):
                logger.error("Port 5050 is still in use. Backend may not have shut down properly.")
            else:
                logger.info("Backend successfully shut down. Port 5050 is free.")

    def is_port_in_use(self, port):
        """Check if a port is in use."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('127.0.0.1', port)) == 0

    # ---------------------- Model Initialization ----------------------

    def load_mode(self):
         # Call backend to load images
        try:
            response = requests.post("http://127.0.0.1:5050/load-model", json={"model": ModelTypes.CLIP.value})
            if response.status_code == 200:
                self.status = StateTypes.MODEL_LOADING
                self.status_label.setText(self.status.value)
                logger.info(f"Backend response: {response.json().get('message')}")
                # Start polling backend for model status every 2 seconds
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
            response = requests.get("http://127.0.0.1:5050/model-status")
            if response.status_code == 200:
                status = response.json().get("status")
                self.status_label.setText(status)
                if status == StateTypes.MODEL_LOADED.value:
                    self.status = StateTypes.MODEL_LOADED
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
        self.status_label = QLabel()
        layout.addWidget(self.status_label)

    def load_stylesheet(self):
        """Load QSS stylesheet for styling."""
        qss_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'styles.qss')
        if os.path.exists(qss_path):
            with open(qss_path, "r") as file:
                return file.read()
        logger.info("Warning: Stylesheet not found.")
        return ""

    def select_folder(self):
        """Select the target folder and notify backend to load images."""
        folder = QFileDialog.getExistingDirectory(self, "Select Target Directory")
        if folder:
            self.target_entry.setText(folder)
            logger.info(f"Selected folder: {folder}")
            # Start polling model status before loading images
            self.start_loading_images()

    def start_loading_images(self):
        """Start polling backend for model status every 2 seconds until ready to load images."""
        self.status_check_timer = QTimer(self)
        self.status_check_timer.timeout.connect(self.check_status_and_load_images)
        self.status_check_timer.start(2000)  # Poll every 2 seconds

    def check_status_and_load_images(self):
        """Check if model is loaded and trigger image loading if ready."""
        try:
            if self.status == StateTypes.MODEL_LOADED:
                self.status_check_timer.stop()  # Stop polling
                self.load_images(self.target_entry.text().strip())  # Trigger image load
            else:
                logger.info("Status: Model is loading.")
        except Exception as e:
            logger.error(f"Failed to check status: {e}")

    def load_images(self, folder):
        """Send a request to backend to load images from selected folder."""
        logger.info(f"Sending load-images request for folder: {folder}")
        try:
            response = requests.post("http://127.0.0.1:5050/load-images", json={"target_folder": folder})
            if response.status_code == 200:
                message = response.json().get('message', "Images loaded.")
                logger.info(f"Backend response: {message}")
                self.status = StateTypes.IMAGES_LOADED
                self.status_label.setText(self.status.value)
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
        target_folder = self.target_entry.text().strip()
        if not target_folder:
            QMessageBox.warning(self, "Warning", "Please select a target folder.")
            return

        if self.status != StateTypes.IMAGES_LOADED:
            QMessageBox.warning(self, "Warning", "Images are not loaded yet. Please try again later.")
            return

        # Step 2: Collect folders/prompts
        self.target_folder = target_folder
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
        self.status_label.setText("Starting categorization...")

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
        self.status_label.setText(f"Processing folder: {output['folder_name']}")

        # Step 4.1: Trigger the job
        try:
            response = requests.post("http://127.0.0.1:5050/start-process", json={
                "target_folder": self.target_folder,
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
                response = requests.get(f"http://127.0.0.1:5050/process-status?folder={folder_name}")
                if response.status_code == 200:
                    status = response.json().get('status')
                    logger.info(f"Status for {folder_name}: {status}")

                    if status == "completed":
                        # Step 4.3: Move to next output
                        self.status_label.setText(f"Completed: {folder_name}")
                        self.progress_bar.setValue(self.current_output_index + 1)
                        self.move_to_next_output()

                    elif status == "error":
                        self.status_label.setText(f"Error processing {folder_name}")
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
        self.status_label.setText("Categorization completed!")
        self.progress_bar.setValue(len(self.outputs))  # Full progress bar

        # Step 5: Reset interface
        self.layout().removeWidget(self.progress_bar)
        self.progress_bar.deleteLater()
        self.progress_bar = None

        self.target_entry.clear()
        for _, _, frame in self.output_fields:
            frame.deleteLater()
        self.output_fields.clear()
        self.status = StateTypes.MODEL_LOADED  # Reset status

        # Optional: Ask to open folder
        choice = QMessageBox.question(self, "Open Folder", "Open target folder now?",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if choice == QMessageBox.StandardButton.Yes:
            os.system(f'open "{self.target_folder}"')  # MacOS, use 'xdg-open' for Linux


# ---------------------- Main App Runner ----------------------

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PhotoCategorizerApp()
    window.show()
    sys.exit(app.exec())
