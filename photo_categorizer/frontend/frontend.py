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
from PyQt6.QtCore import Qt
from photo_categorizer.logger import logger




class PhotoCategorizerApp(QWidget):
    def __init__(self):
        super().__init__()

        # Backend initialization
        self.backend_process = self.start_backend()

        # GUI setup
        self.setStyleSheet(self.load_stylesheet())
        self.setWindowTitle("Photo Categorizer")
        self.setGeometry(200, 200, 800, 600)
        self.output_fields = []

        self.build_ui()

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
            QMessageBox.critical(self, "Error", "Failed to start backend. Please check backend.py")
            sys.exit(1)

        return backend_process

    def wait_for_backend(self, url='http://127.0.0.1:5050/', timeout=10):
        """Wait until backend is ready to accept requests."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url)
                if response.status_code in (200, 404):  # 404 is acceptable (if root route isn't defined)
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

    def load_stylesheet(self):
        """Load QSS stylesheet for styling."""
        qss_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'styles.qss')
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

            # Call backend to load images
            try:
                response = requests.post("http://127.0.0.1:5050/load-images", json={"target_folder": folder})
                if response.status_code == 200:
                    QMessageBox.information(self, "Success", response.json().get("message", "Images loaded."))
                    logger.info(f"Backend response: {response.json().get('message')}")
                else:
                    error_msg = response.json().get('error', 'Unknown error')
                    QMessageBox.critical(self, "Error", f"Failed to load images: {error_msg}")
                    logger.error(f"Backend error: {error_msg}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to connect to backend: {e}")
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
        """Collect data and send categorization request."""
        target_folder = self.target_entry.text().strip()
        if not target_folder:
            QMessageBox.warning(self, "Warning", "Please select a target folder.")
            return

        outputs = [
            {"folder_name": fn.text().strip(), "prompt": pr.text().strip()}
            for fn, pr, _ in self.output_fields if fn.text().strip() and pr.text().strip()
        ]

        if not outputs:
            QMessageBox.warning(self, "Warning", "Please add at least one output folder and prompt.")
            return

        data = {"target_folder": target_folder, "outputs": outputs}
        logger.info(f"Sending data to backend:{data}")

        try:
            response = requests.post("http://127.0.0.1:5050/categorize", json=data)
            if response.status_code == 200:
                QMessageBox.information(self, "Success", response.json().get("message", "Categorization completed."))
            else:
                error_msg = response.json().get('error', 'Unknown error')
                QMessageBox.critical(self, "Error", f"Error: {error_msg}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to connect to backend: {e}")


# ---------------------- Main App Runner ----------------------

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PhotoCategorizerApp()
    window.show()
    sys.exit(app.exec())
