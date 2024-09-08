import os
import json
import shutil
import sys
import pandas as pd
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QPushButton, 
                               QFormLayout, QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QMessageBox, 
                               QComboBox, QDialog, QHBoxLayout, QLabel)
from PySide6.QtCore import Qt

class ReviewDialog(QDialog):
    def __init__(self, data, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Review Excel Data')
        self.setGeometry(100, 100, 600, 400)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.form_layout = QFormLayout()
        self.layout.addLayout(self.form_layout)

        for index, row in data.iterrows():
            show_name = row.get('SHOW', '')
            shot_name = row.get('SHOT', '')
            resolution = row.get('RESOLUTION', '')
            frame_range = row.get('FRAME-RANGE', '')
            comment = row.get('COMMENTS', '')  # Added to review comments

            form_row = QHBoxLayout()
            form_row.addWidget(QLabel(f'Show: {show_name}'))
            form_row.addWidget(QLabel(f'Shot: {shot_name}'))
            form_row.addWidget(QLabel(f'Resolution: {resolution}'))
            form_row.addWidget(QLabel(f'Frame Range: {frame_range}'))
            form_row.addWidget(QLabel(f'Comments: {comment}'))  # Display comments
            
            self.form_layout.addRow(form_row)

        button_layout = QHBoxLayout()
        self.layout.addLayout(button_layout)

        self.yes_button = QPushButton('Yes')
        self.yes_button.clicked.connect(self.accept)
        button_layout.addWidget(self.yes_button)

        self.no_button = QPushButton('No')
        self.no_button.clicked.connect(self.reject)
        button_layout.addWidget(self.no_button)

class ShowShotManager(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Show and Shot List Manager')
        self.setGeometry(100, 100, 1000, 850)

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)

        self.layout = QVBoxLayout()
        self.main_widget.setLayout(self.layout)

        self.form_layout = QFormLayout()

        self.project_path_input = QLineEdit()
        self.browse_button = QPushButton('Browse...')
        self.browse_button.clicked.connect(self.browse_project_path)
        
        self.load_excel_button = QPushButton('Load from Excel')
        self.load_excel_button.clicked.connect(self.load_from_excel)
        
        self.show_input = QLineEdit()
        self.shot_input = QLineEdit()
        self.frame_range_input = QLineEdit()
        self.comment_input = QLineEdit()
        self.resolution_dropdown = QComboBox()
        self.resolution_dropdown.addItems(['2K', '4K', 'HD', 'Custom'])
        self.custom_resolution_input = QLineEdit()
        self.custom_resolution_input.setPlaceholderText('Enter custom resolution (e.g., 2048x1536)')
        self.custom_resolution_input.setEnabled(False)
        self.resolution_dropdown.currentIndexChanged.connect(self.on_resolution_change)

        self.form_layout.addRow('Project Path:', self.project_path_input)
        self.form_layout.addWidget(self.browse_button)
        self.form_layout.addWidget(self.load_excel_button)
        self.form_layout.addRow('Show Name:', self.show_input)
        self.form_layout.addRow('Shot Name:', self.shot_input)
        self.form_layout.addRow('Frame Range:', self.frame_range_input)
        self.form_layout.addRow('Comment:', self.comment_input)
        self.form_layout.addRow('Resolution:', self.resolution_dropdown)
        self.form_layout.addWidget(self.custom_resolution_input)

        self.add_button = QPushButton('Add Shot')
        self.add_button.clicked.connect(self.add_shot)
        self.form_layout.addWidget(self.add_button)

        self.add_plates_button = QPushButton('Add Plates')
        self.add_plates_button.clicked.connect(self.add_footage)
        self.form_layout.addWidget(self.add_plates_button)

        self.add_elements_button = QPushButton('Add Elements')
        self.add_elements_button.clicked.connect(self.add_elements)
        self.form_layout.addWidget(self.add_elements_button)

        self.show_dropdown = QComboBox()
        self.show_dropdown.currentIndexChanged.connect(self.show_dropdown_changed)
        self.form_layout.addRow('Select Show:', self.show_dropdown)

        self.layout.addLayout(self.form_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(['Show', 'Shot', 'Frame Range', 'Comment', 'Resolution', 'Actions'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.table)

        self.shows = {}  # Store shows and shots
        self.project_path = ''
        self.metadata_path = os.path.join(os.path.expanduser('~/.nuke'), 'metadata')
        os.makedirs(self.metadata_path, exist_ok=True)

        self.load_existing_shows()

    def browse_project_path(self):
        path = QFileDialog.getExistingDirectory(self, 'Select Project Directory')
        if path:
            self.project_path_input.setText(path)
            self.project_path = path

    def on_resolution_change(self):
        self.custom_resolution_input.setEnabled(self.resolution_dropdown.currentText() == 'Custom')

    def add_shot(self):
        show_name = self.show_input.text().strip()
        shot_name = self.shot_input.text().strip()
        frame_range = self.frame_range_input.text().strip()
        comment = self.comment_input.text().strip()
        resolution = self.custom_resolution_input.text().strip() if self.resolution_dropdown.currentText() == 'Custom' else self.resolution_dropdown.currentText()

        if not self.project_path:
            QMessageBox.warning(self, 'Warning', 'Please select a project directory.')
            return

        if not show_name or not shot_name:
            QMessageBox.warning(self, 'Warning', 'Please enter both show name and shot name.')
            return

        if show_name not in self.shows:
            self.shows[show_name] = []

        self.shows[show_name].append({
            'shot': shot_name,
            'frame_range': frame_range,
            'comment': comment,
            'resolution': resolution,
            'footage': '',  
            'elements': '',  
            'path': os.path.join(self.project_path, show_name, shot_name)
        })

        self.create_folder_structure(show_name, shot_name)
        self.create_metadata_file(show_name, shot_name, frame_range, comment, resolution, '', '')

        self.update_table()
        self.clear_inputs()
        self.update_show_dropdown()

    def create_folder_structure(self, show_name, shot_name):
        folders = ['comp', 'fx', 'lighting', 'roto', 'prep', 'footages', 'elements']
        software_folders = ['nuke', 'houdini', 'silhouette', 'mari', 'substance', 'katana']
        
        shot_path = os.path.join(self.project_path, show_name, shot_name)

        if not os.path.exists(shot_path):
            os.makedirs(shot_path)

        for folder in folders + software_folders:
            folder_path = os.path.join(shot_path, folder)
            os.makedirs(folder_path, exist_ok=True)

    def create_metadata_file(self, show_name, shot_name, frame_range, comment, resolution, footage_path, elements_path):
        metadata = {
            'show': show_name,
            'shot': shot_name,
            'frame_range': frame_range,
            'comment': comment,
            'resolution': resolution,
            'footage': footage_path,
            'elements': elements_path,
            'path': os.path.join(self.project_path, show_name, shot_name)
        }

        metadata_file = os.path.join(self.metadata_path, f'{show_name}_{shot_name}_metadata.json')

        with open(metadata_file, 'w') as file:
            json.dump(metadata, file, indent=4)

    def add_footage(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, 'Warning', 'Please select a row in the table.')
            return
        
        show_name = self.table.item(selected_row, 0).text()
        shot_name = self.table.item(selected_row, 1).text()

        footage_path, _ = QFileDialog.getOpenFileName(self, 'Select Footage File')
        if footage_path:
            self.shows[show_name][selected_row]['footage'] = footage_path
            metadata_file = os.path.join(self.metadata_path, f'{show_name}_{shot_name}_metadata.json')

            with open(metadata_file, 'r') as file:
                metadata = json.load(file)

            metadata['footage'] = footage_path

            with open(metadata_file, 'w') as file:
                json.dump(metadata, file, indent=4)

            self.update_table()

    def add_elements(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, 'Warning', 'Please select a row in the table.')
            return
        
        show_name = self.table.item(selected_row, 0).text()
        shot_name = self.table.item(selected_row, 1).text()

        elements_path, _ = QFileDialog.getExistingDirectory(self, 'Select Elements Directory')
        if elements_path:
            self.shows[show_name][selected_row]['elements'] = elements_path
            metadata_file = os.path.join(self.metadata_path, f'{show_name}_{shot_name}_metadata.json')

            with open(metadata_file, 'r') as file:
                metadata = json.load(file)

            metadata['elements'] = elements_path

            with open(metadata_file, 'w') as file:
                json.dump(metadata, file, indent=4)

            self.update_table()

    def update_table(self, selected_show=None):
        """Update the table with shots, optionally filtered by the selected show."""
        self.table.setRowCount(0)  # Clear the table

        for show_name, shots in self.shows.items():
            if selected_show and show_name != selected_show:
                continue  # Skip shots not belonging to the selected show

            for shot in shots:
                row_position = self.table.rowCount()
                self.table.insertRow(row_position)

                self.table.setItem(row_position, 0, QTableWidgetItem(show_name))
                self.table.setItem(row_position, 1, QTableWidgetItem(shot['shot']))
                self.table.setItem(row_position, 2, QTableWidgetItem(shot['frame_range']))
                self.table.setItem(row_position, 3, QTableWidgetItem(shot['comment']))  # Comment in table
                self.table.setItem(row_position, 4, QTableWidgetItem(shot['resolution']))

                remove_button = QPushButton('Remove')
                remove_button.clicked.connect(lambda ch, row=row_position: self.remove_shot(row))
                self.table.setCellWidget(row_position, 5, remove_button)

        


    def remove_shot(self, row):
        show_name = self.table.item(row, 0).text()
        shot_name = self.table.item(row, 1).text()

        confirm = QMessageBox.question(self, 'Confirm', f'Are you sure you want to remove {show_name} - {shot_name}?',
                                       QMessageBox.Yes | QMessageBox.No)

        if confirm == QMessageBox.Yes:
            shot_path = self.shows[show_name][row]['path']

            if os.path.exists(shot_path):
                shutil.rmtree(shot_path)  # Delete entire folder structure
            
            metadata_file = os.path.join(self.metadata_path, f'{show_name}_{shot_name}_metadata.json')
            if os.path.exists(metadata_file):
                os.remove(metadata_file)  # Remove metadata file

            del self.shows[show_name][row]
            self.update_table()

    def clear_inputs(self):
        self.show_input.clear()
        self.shot_input.clear()
        self.frame_range_input.clear()
        self.comment_input.clear()  # Clear comment input
        self.resolution_dropdown.setCurrentIndex(0)
        self.custom_resolution_input.clear()

    def load_existing_shows(self):
        if not os.path.exists(self.metadata_path):
            return

        for metadata_file in os.listdir(self.metadata_path):
            if metadata_file.endswith('_metadata.json'):
                with open(os.path.join(self.metadata_path, metadata_file), 'r') as file:
                    metadata = json.load(file)

                show_name = metadata['show']
                shot_name = metadata['shot']
                frame_range = metadata['frame_range']
                comment = metadata.get('comment', '')  # Load comment
                resolution = metadata['resolution']
                footage = metadata.get('footage', '')
                elements = metadata.get('elements', '')
                path = metadata['path']

                if show_name not in self.shows:
                    self.shows[show_name] = []

                self.shows[show_name].append({
                    'shot': shot_name,
                    'frame_range': frame_range,
                    'comment': comment,
                    'resolution': resolution,
                    'footage': footage,
                    'elements': elements,
                    'path': path
                })

        self.update_table()
        self.update_show_dropdown()

    def load_from_excel(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Select Excel File', '', 'Excel Files (*.xlsx)')

        if not file_path:
            return

        df = pd.read_excel(file_path)
        required_columns = ['SHOW', 'SHOT', 'RESOLUTION', 'FRAME-RANGE', 'COMMENTS']
        if not all(column in df.columns for column in required_columns):
            QMessageBox.warning(self, 'Warning', 'Excel file must contain the columns: SHOW, SHOT, RESOLUTION, FRAME-RANGE, COMMENTS.')
            return

        review_dialog = ReviewDialog(df, self)
        if review_dialog.exec_() == QDialog.Accepted:
            for _, row in df.iterrows():
                show_name = row['SHOW']
                shot_name = row['SHOT']
                resolution = row['RESOLUTION']
                frame_range = row['FRAME-RANGE']
                comment = row['COMMENTS']  # Load comment from Excel

                if show_name not in self.shows:
                    self.shows[show_name] = []

                self.shows[show_name].append({
                    'shot': shot_name,
                    'frame_range': frame_range,
                    'comment': comment,  # Add comment field
                    'resolution': resolution,
                    'footage': '',
                    'elements': '',
                    'path': os.path.join(self.project_path, show_name, shot_name)
                })

                self.create_folder_structure(show_name, shot_name)
                self.create_metadata_file(show_name, shot_name, frame_range, comment, resolution, '', '')

            self.update_table()
            self.update_show_dropdown()

    def update_show_dropdown(self):
        current_show = self.show_dropdown.currentText()
        self.show_dropdown.clear()
        self.show_dropdown.addItems(self.shows.keys())

        if current_show in self.shows:
            self.show_dropdown.setCurrentText(current_show)

    def show_dropdown_changed(self, index):
        """Filter the shots based on the selected show in the dropdown."""
        selected_show = self.show_dropdown.currentText()
        self.update_table(selected_show)  # Update table with shots from selected show

if __name__ == '__main__':
    app = QApplication(sys.argv)
    manager = ShowShotManager()
    manager.show()
    sys.exit(app.exec())
