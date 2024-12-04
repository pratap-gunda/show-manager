# ~/.nuke/custom_tools/smart_save.py

import os
import json
import nuke
import PySide2.QtWidgets as QtWidgets

class SaveDialog(QtWidgets.QDialog):
    def __init__(self, default_name, parent=None):
        super(SaveDialog, self).__init__(parent)
        self.setWindowTitle('Save Nuke Script')
        self.setGeometry(100, 100, 400, 150)

        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        self.info_label = QtWidgets.QLabel(f"Current Name: {default_name}")
        self.layout.addWidget(self.info_label)

        self.suffix_label = QtWidgets.QLabel('Suffix:')
        self.suffix_input = QtWidgets.QLineEdit()
        self.layout.addWidget(self.suffix_label)
        self.layout.addWidget(self.suffix_input)

        self.final_path_label = QtWidgets.QLabel('')
        self.layout.addWidget(self.final_path_label)

        self.button_layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.button_layout)

        self.save_button = QtWidgets.QPushButton('Save')
        self.save_button.clicked.connect(self.accept)
        self.button_layout.addWidget(self.save_button)

        self.cancel_button = QtWidgets.QPushButton('Cancel')
        self.cancel_button.clicked.connect(self.reject)
        self.button_layout.addWidget(self.cancel_button)

    def get_suffix(self):
        return self.suffix_input.text().strip()

    def set_final_path(self, path):
        self.final_path_label.setText(f"Final Path: {path}")

def smart_save():
    # Get the current Nuke script directory
    current_script_path = nuke.root().name()

    # Check if a script is open
    if not current_script_path:
        nuke.message("No script is currently open.")
        return

    # Determine metadata file
    metadata_path = os.path.expanduser('~/.nuke/metadata')
    if not os.path.exists(metadata_path):
        nuke.message("Metadata directory does not exist.")
        return

    metadata_files = [f for f in os.listdir(metadata_path) if f.endswith('_metadata.json')]
    if not metadata_files:
        nuke.message("No metadata files found.")
        return

    # Find the metadata file corresponding to the current script
    metadata_file = None
    for file in metadata_files:
        if file.startswith(os.path.basename(current_script_path).split('_')[0]):
            metadata_file = os.path.join(metadata_path, file)
            break

    if not metadata_file:
        nuke.message("Metadata file not found for the current script.")
        return

    # Load metadata
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)

    shot_path = metadata.get('path', '')
    if not shot_path:
        nuke.message("Path not found in metadata.")
        return

    # Construct the default name for saving
    description = nuke.getInput('Script description', 'bashComp').strip().replace(' ', '')
    if not description:
        nuke.message("No description provided.")
        return

    default_name = f"{os.path.basename(shot_path)}_{description}_v01.nk"
    comp_path = os.path.join(shot_path, 'comp')

    # Open save dialog
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    dialog = SaveDialog(default_name)
    dialog.set_final_path(os.path.join(comp_path, default_name))

    if dialog.exec_() == QtWidgets.QDialog.Accepted:
        suffix = dialog.get_suffix()
        version = 1
        while True:
            nk_name = f"{default_name.replace('_v01.nk', f'_{suffix}_v{version:02d}.nk')}"
            nk_path = os.path.join(comp_path, nk_name)

            if not os.path.isfile(nk_path):
                nuke.scriptSaveAs(nk_path)
                nuke.message(f"Script saved as {nk_path}")
                break

            version += 1
