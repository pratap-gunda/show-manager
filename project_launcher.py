import os
import json
import sys
import subprocess
from functools import partial
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, QComboBox, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QPushButton, QMessageBox, QHBoxLayout, QLabel, 
                               QMenu)
from PySide6.QtGui import QIcon, QPixmap, QCursor
from PySide6.QtCore import Qt, QSize, QPoint

class ProjectLauncher(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Project Launcher')
        self.setGeometry(100, 100, 1200, 800)

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)

        self.layout = QVBoxLayout()
        self.main_widget.setLayout(self.layout)

        # Dropdown menu for selecting show
        self.show_dropdown = QComboBox()
        self.show_dropdown.currentIndexChanged.connect(self.load_shots_for_show)
        self.layout.addWidget(self.show_dropdown)

        # Table for displaying shots
        self.table = QTableWidget()
        self.table.setColumnCount(6)  # 5 columns for data + 1 column for buttons
        self.table.setHorizontalHeaderLabels(['Show', 'Shot', 'Frame Range', 'Comment', 'Resolution', 'Launch'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.cellClicked.connect(self.on_table_cell_clicked)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.on_right_click)
        self.layout.addWidget(self.table)

        # Metadata display form
        self.form_widget = QWidget()
        self.form_layout = QVBoxLayout()
        self.form_widget.setLayout(self.form_layout)
        self.layout.addWidget(self.form_widget)

        self.frame_range_label = QLabel('Frame Range:')
        self.resolution_label = QLabel('Resolution:')

        self.form_layout.addWidget(self.frame_range_label)
        self.form_layout.addWidget(self.resolution_label)

        # Load project data
        self.shows = {}
        self.metadata_path = os.path.join(os.path.expanduser('~/.nuke'), 'metadata')
        self.load_shows()

    def load_shows(self):
        if not os.path.exists(self.metadata_path):
            QMessageBox.warning(self, 'Warning', 'Metadata directory does not exist.')
            return

        # Load all metadata files
        for metadata_file in os.listdir(self.metadata_path):
            if metadata_file.endswith('_metadata.json'):
                with open(os.path.join(self.metadata_path, metadata_file), 'r') as file:
                    metadata = json.load(file)
                    show_name = metadata['show']
                    if show_name not in self.shows:
                        self.shows[show_name] = []
                    self.shows[show_name].append(metadata)

        self.show_dropdown.addItems(sorted(self.shows.keys()))

    def load_shots_for_show(self):
        show_name = self.show_dropdown.currentText()
        if show_name in self.shows:
            self.update_table(self.shows[show_name])
        else:
            self.table.setRowCount(0)

    def update_table(self, shots):
        self.table.setRowCount(0)

        for shot in shots:
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)

            self.table.setItem(row_position, 0, QTableWidgetItem(shot.get('show', '')))
            self.table.setItem(row_position, 1, QTableWidgetItem(shot.get('shot', '')))
            self.table.setItem(row_position, 2, QTableWidgetItem(shot.get('frame_range', '')))
            self.table.setItem(row_position, 3, QTableWidgetItem(shot.get('comment', '')))
            self.table.setItem(row_position, 4, QTableWidgetItem(shot.get('resolution', '')))

            # Add software buttons in the 'Launch' column
            self.add_software_buttons(row_position, shot)

    def add_software_buttons(self, row, shot):
        # Clear previous buttons
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        icons = {
            'nuke': r'C:\Users\vishr\Documents\project manager python\pratap\show_manager\icons/oundry_n_icon.png',
            'houdini': r'C:\Users\vishr\Documents\project manager python\pratap\show_manager\icons/houdini_icon.png',
            'substance': r'C:\Users\vishr\Documents\project manager python\pratap\show_manager\icons/substance_icon.png',
            'katana': r'C:\Users\vishr\Documents\project manager python\pratap\show_manager\icons/katana_icon.jpeg'
        }

        for software, icon_path in icons.items():
            button = QPushButton()
            button.setIcon(QIcon(icon_path))
            button.setIconSize(QSize(32, 32))
            button.clicked.connect(partial(self.launch_software, software, shot))
            layout.addWidget(button)

        widget.setLayout(layout)
        self.table.setCellWidget(row, 5, widget)

    def on_table_cell_clicked(self, row, column):
        if column == 1:  # Show metadata when clicking on 'Shot' column
            show_name = self.show_dropdown.currentText()
            self.current_row = row
            self.current_shot = next(shot for shot in self.shows[show_name] if shot.get('shot') == self.table.item(row, 1).text())
            self.frame_range_label.setText(f"Frame Range: {self.current_shot.get('frame_range', '')}")
            self.resolution_label.setText(f"Resolution: {self.current_shot.get('resolution', '')}")

    def on_right_click(self, position):
        index = self.table.indexAt(position)
        if index.isValid():
            shot_name = self.table.item(index.row(), 1).text()
            menu = QMenu()
            select_scripts_action = menu.addAction("Select Scripts")
            select_scripts_action.triggered.connect(partial(self.show_scripts_in_comp_folder, shot_name))
            menu.exec(QCursor.pos())

    def show_scripts_in_comp_folder(self, shot_name):
        comp_folder = os.path.join(r'C:\Users\vishr\Documents\project manager python\pratap\projects\DIG', f'DIG_{shot_name}', 'comp')
        
        if not os.path.exists(comp_folder):
            QMessageBox.warning(self, 'Error', f'Comp folder does not exist for shot: {shot_name}')
            return

        scripts = [f for f in os.listdir(comp_folder) if f.endswith('.nk')]
        
        if not scripts:
            QMessageBox.information(self, 'No Scripts', 'No Nuke scripts found in the comp folder.')
            return

        script_menu = QMenu()

        for script in scripts:
            script_action = script_menu.addAction(script)
            script_action.triggered.connect(partial(self.open_nuke_script, os.path.join(comp_folder, script)))

        script_menu.exec(QCursor.pos())

    def open_nuke_script(self, script_path):
        try:
            subprocess.run([r'C:\Program Files\Nuke15.1v2\Nuke15.1.exe', script_path], check=True)
        except subprocess.CalledProcessError as e:
            QMessageBox.warning(self, 'Error', f'Failed to open Nuke script: {e}')

    def launch_software(self, software_name, shot):
        # Path to executable for each software
        software_paths = {
            'nuke': r'C:\Program Files\Nuke15.1v2\Nuke15.1.exe',
            'houdini': r'C:\Program Files\Houdini_19.5\bin\houdinifx.exe',
            'substance': r'C:\Program Files\Substance\SubstancePainter.exe',
            'katana': r'C:\Program Files\Katana\katana.exe'
        }

        # Get metadata path
        show_name = self.show_dropdown.currentText()
        shot_number = shot.get('shot', '').replace(' ', '_')
        metadata_file = f"{show_name}_{shot_number}_metadata.json"
        metadata_path = os.path.join(self.metadata_path, metadata_file)

        if software_name == 'nuke':
            # Ensure metadata file exists
            if os.path.exists(metadata_path):
                # Load metadata
                with open(metadata_path, 'r') as file:
                    metadata = json.load(file)
                
                # Extract metadata values
                frame_range = metadata.get('frame_range', '1001-1100')
                resolution = metadata.get('resolution', '2K')
                shot_path = metadata.get('path', '')

                # Create a temporary script to set project settings in Nuke
                temp_script_path = os.path.join(os.path.expanduser('~'), 'set_project_settings.py')

                # Split frame range into start and end frames
                try:
                    start_frame, end_frame = map(int, frame_range.split('-'))
                except ValueError:
                    start_frame = 1001
                    end_frame = 1100
                    print('Error: Frame range format is incorrect. Using default values.')

                # Write script content
                script_content = f"""
import nuke

# Open the template
nuke.scriptOpen('C:/Users/vishr/Documents/project manager python/pratap/nuke_templete/empty_templete_updated.nk')

# Access project settings
project_settings = nuke.root()

# Set metadata values
project_settings['first_frame'].setValue({start_frame})
project_settings['last_frame'].setValue({end_frame})

# Set resolution
if "{resolution}" == "2K":
    project_settings['format'].setValue('2K_DCP')
elif "{resolution}" == "4K":
    project_settings['format'].setValue('4K_DCP')
elif "{resolution}" == "HD":
    project_settings['format'].setValue('HD_1080')
else:
    print('Error: Resolution value is invalid.')

# Set additional metadata
project_settings['label'].setValue(f"Show: {metadata.get('show')}  Shot: {metadata.get('shot')}")

# Save the modified script to the shot's Nuke script folder
script_path = os.path.join("{shot_path}", "comp", "{shot_number}_v001.nk")
nuke.scriptSaveAs(script_path)
                """
                with open(temp_script_path, 'w') as script_file:
                    script_file.write(script_content)

                # Launch Nuke with the metadata and run the script
                command = [
                    software_paths[software_name],
                    '-run', temp_script_path
                ]

                try:
                    subprocess.run(command, check=True)
                except subprocess.CalledProcessError as e:
                    QMessageBox.warning(self, 'Error', f'Failed to launch Nuke with metadata: {e}')
                finally:
                    os.remove(temp_script_path)  # Clean up the temporary script
            else:
                QMessageBox.warning(self, 'Error', 'Metadata file does not exist.')

        else:
            if software_name in software_paths:
                command = [software_paths[software_name]]
                try:
                    subprocess.run(command, check=True)
                except subprocess.CalledProcessError as e:
                    QMessageBox.warning(self, 'Error', f'Failed to launch {software_name}: {e}')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ProjectLauncher()
    window.show()
    sys.exit(app.exec())
