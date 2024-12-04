# ~/.nuke/menu.py
import nuke
import subprocess
import os

import sys
import os
import nuke
import PySide2.QtWidgets as QtWidgets

# Add the custom_tools directory to the system path
custom_tools_path = os.path.join(os.path.expanduser('~/.nuke'), 'custom_tools')
if custom_tools_path not in sys.path:
    sys.path.append(custom_tools_path)

# Import the custom tool

import smart_save

# Define the custom save function
def custom_save_as():
    smart_save.smart_save()

# Override the default 'Save As' command with the custom one
nuke.menu('Nuke').addCommand('File/Save As', custom_save_as, 'Ctrl+Shift+S')

# Optionally, add a command to open the default save dialog
nuke.menu('Nuke').addCommand('File/Default Save As', 'nuke.scriptSaveAs', 'Ctrl+S')


# Import the main script for the ComfyUI tool
import comfy_nuke_prompt_main

# Add the custom menu
def add_menu():
    import nuke
    # Check if 'comfy_tools' menu already exists, if not, create it
    menu = nuke.menu('Nuke')
    comfy_tools = menu.findItem('comfy_tools')
    if comfy_tools is None:
        comfy_tools = menu.addMenu('comfy_tools')

    # Add 'comfy_nuke_prompt' to 'comfy_tools'
    comfy_tools.addCommand('comfy_nuke_prompt', comfy_nuke_prompt_main.show_nuke_ui)

# Add the menu when Nuke starts
add_menu()


import nuke
import os

# Define a function to launch your UI
def launch_my_ui():
    script_path = os.path.join(os.path.expanduser("~"), ".nuke", "test_ui.py")
    exec(open(script_path).read())

# Add a menu item to the Nuke menu to launch the UI
nuke.menu('Nuke').addCommand('Custom/Run Script GUI', launch_my_ui)







