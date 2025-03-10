import os
import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton,
    QFileDialog, QLineEdit, QMessageBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt
import requests
import subprocess
import signal
import atexit


class PhotoCategorizerApp(QWidget):
    def __init__(self):
        super().__init__()

        # Start Flask backend
        self.backend_process = subprocess.Popen(
            [sys.executable, "photo_categorizer/backend.py"],  # Adjust path if needed
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        # Register a cleanup function to close backend when frontend exits
        atexit.register(self.cleanup_backend)

        self.setStyleSheet(self.load_stylesheet())
        self.setWindowTitle("Photo Categorizer")
        self.setGeometry(200, 200, 800, 600)
        self.output_fields = []

        layout = QVBoxLayout(self)

        # Target folder section
        target_layout = QHBoxLayout()
        target_layout.setContentsMargins(0, 0, 0, 0)
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

        # Add initial output input
        self.add_output_input()

        # Add filter button
        add_button = QPushButton("Add Filter")
        add_button.clicked.connect(self.add_output_input)
        layout.addWidget(add_button)

        # Start button
        start_button = QPushButton("Start Categorization")
        start_button.clicked.connect(self.start_categorization)
        layout.addWidget(start_button)

    def cleanup_backend(self):
        if self.backend_process:
            print("Shutting down backend...")
            self.backend_process.terminate()  # Gracefully ask to stop
            try:
                self.backend_process.wait(timeout=5)  # Wait a bit for graceful exit
            except subprocess.TimeoutExpired:
                print("Force killing backend...")
                self.backend_process.kill()  # Force kill if needed


    def load_stylesheet(self):
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        qss_path = os.path.join(BASE_DIR, "styles.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r") as file:
                return file.read()
        else:
            print("Warning: Stylesheet not found.")
            return ""

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Target Directory")
        if folder:
            self.target_entry.setText(folder)

    def add_output_input(self):
        # Frame for each filter row
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
        label_folder = QLabel("Folder Name:")
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
        # Find and remove the corresponding frame
        for i, (_, _, frm) in enumerate(self.output_fields):
            if frm == frame:
                self.output_fields.pop(i)
                break
        self.scroll_layout.removeWidget(frame)
        frame.deleteLater()

    def start_categorization(self):
        target_folder = self.target_entry.text().strip()
        if not target_folder:
            QMessageBox.warning(self, "Warning", "Please select a target folder.")
            return

        outputs = []
        for folder_input, prompt_input, _ in self.output_fields:
            folder_name = folder_input.text().strip()
            prompt = prompt_input.text().strip()
            if folder_name and prompt:
                outputs.append({"folder_name": folder_name, "prompt": prompt})

        if not outputs:
            QMessageBox.warning(self, "Warning", "Please add at least one output folder and prompt.")
            return

        data = {
            "target_folder": target_folder,
            "outputs": outputs
        }

        # Send to Flask backend
        try:
            response = requests.post("http://127.0.0.1:5000/categorize", json=data)
            if response.status_code == 200:
                QMessageBox.information(self, "Success", response.json().get("message", "Categorization completed."))
            else:
                QMessageBox.critical(self, "Error", f"Error: {response.json().get('error', 'Unknown error')}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to connect backend: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PhotoCategorizerApp()
    window.show()
    sys.exit(app.exec())
