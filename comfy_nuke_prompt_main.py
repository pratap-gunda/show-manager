import sys
import uuid
import json
import urllib.request
import urllib.parse
import requests
import websocket  # NOTE: websocket-client (https://github.com/websocket-client/websocket-client)
from PIL import Image
import io
import random
import os
import subprocess
from PySide2 import QtWidgets, QtCore, QtGui

server_address = "127.0.0.1:8188"
client_id = str(uuid.uuid4())

def queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"http://{server_address}/prompt", data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_image(filename, subfolder, folder_type):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen(f"http://{server_address}/view?{url_values}") as response:
        return response.read()

def get_history(prompt_id):
    with urllib.request.urlopen(f"http://{server_address}/history/{prompt_id}") as response:
        return json.loads(response.read())

def get_images(ws, prompt):
    prompt_id = queue_prompt(prompt)['prompt_id']
    output_images = {}
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['node'] is None and data['prompt_id'] == prompt_id:
                    break  # Execution is done
        else:
            continue  # previews are binary data

    history = get_history(prompt_id)[prompt_id]
    for o in history['outputs']:
        for node_id in history['outputs']:
            node_output = history['outputs'][node_id]
            if 'images' in node_output:
                images_output = []
                for image in node_output['images']:
                    image_data = get_image(image['filename'], image['subfolder'], image['type'])
                    images_output.append(image_data)
            output_images[node_id] = images_output

    return output_images

def upload_file(file_path, subfolder="", overwrite=False):
    try:
        with open(file_path, "rb") as file:
            body = {"image": file}
            data = {}
            
            if overwrite:
                data["overwrite"] = "true"
    
            if subfolder:
                data["subfolder"] = subfolder
    
            resp = requests.post(f"http://{server_address}/upload/image", files=body, data=data)
            
            if resp.status_code == 200:
                data = resp.json()
                path = data["name"]
                if "subfolder" in data:
                    if data["subfolder"] != "":
                        path = data["subfolder"] + "/" + path
            else:
                print(f"{resp.status_code} - {resp.reason}")
    except Exception as error:
        print(error)
    return path




def get_generative_ai_folder():
    """Retrieve the path to the 'generative_ai' folder."""
    try:
        import nuke

        # Get the full path of the current Nuke script
        nuke_script_path = nuke.root().name()

        if nuke_script_path == "Root":
            nuke.message(f"please launch comfiui from shot environment!")
            raise ValueError("please launch comfiui from shot environment!")
           
        # Extract the root folder of the Nuke script
        root_folder = os.path.dirname(nuke_script_path)
        
        # Go one level up
        parent_folder = os.path.dirname(root_folder)
        
        # Path to the generative_ai folder
        generative_ai_folder = os.path.join(parent_folder, "generative_ai")
        
        # Check if the folder exists
        if not os.path.exists(generative_ai_folder):
            raise FileNotFoundError(f"The 'generative_ai' folder does not exist in {parent_folder}")
        
        return generative_ai_folder

    except Exception as e:
        raise RuntimeError(f"Error determining 'generative_ai' folder: {str(e)}")




def run_image_script(checkpoint, positive_prompt, negative_prompt,save_image_name):
    """Run the image generation script and save the result."""
    try:
        import nuke  # Ensure Nuke module is imported only when running in Nuke

        # Get the current Nuke script name
        nuke_script_name = nuke.root().name()
        
        if nuke_script_name == "Root":  # Handle unsaved scripts
            shot_name = "unsaved_script"
        else:
            shot_name = os.path.splitext(os.path.basename(nuke_script_name))[0]  # Extract shot name without extension

    except ImportError:
        print("Nuke module not found. Running script outside Nuke environment.")
        shot_name = "external_run"  # Fallback name if not in Nuke

    try:
        # Get the path to the generative_ai folder
        generative_ai_folder = get_generative_ai_folder()

        # Update the path to the correct location
        image_path = r"C:\Users\vishr\Documents\comfy_test\example.png"
        
        # Upload an image
        comfyui_path_image = upload_file(image_path, "", True)

        # Load workflow from file
        workflow_path = r"C:\Users\vishr\Documents\comfy_test\workflow.json"
        with open(workflow_path, "r", encoding="utf-8") as f:
            workflow_data = f.read()

        workflow = json.loads(workflow_data)

        # Set the text prompt for positive and negative CLIPTextEncode
        workflow["6"]["inputs"]["text"] = positive_prompt
        workflow["7"]["inputs"]["text"] = negative_prompt

        # Set random seed
        seed = random.randint(1, 1000000000)
        workflow["3"]["inputs"]["seed"] = seed

        # Set the image name for LoadImage node
        #workflow["11"]["inputs"]["image"] = comfyui_path_image
        width = "200"
        height = "200"
        workflow["14"]["inputs"]["width"] = width
        workflow["14"]["inputs"]["height"] = height


        # Set the model
        workflow["4"]["inputs"]["ckpt_name"] = checkpoint

        # Connect to WebSocket and get images
        ws = websocket.WebSocket()
        ws.connect(f"ws://{server_address}/ws?clientId={client_id}")
        images = get_images(ws, workflow)

        # Save images and create Nuke Read node with Backdrop
        for node_id in images:
            for image_data in images[node_id]:
                image = Image.open(io.BytesIO(image_data))
                output_filename = f"{shot_name}_{save_image_name}.png"
                output_path = os.path.join(generative_ai_folder,output_filename ).replace("\\", "/")
                image.save(output_path)
                print(f"Saved image to: {output_path}")

                # Create Nuke Read node with the saved image path
                try:
                    read_node = nuke.createNode('Read')
                    read_node['file'].setValue(output_path)

                    # Create a backdrop node and set its size and position
                    backdrop_node = nuke.createNode('BackdropNode')
                    backdrop_node['label'].setValue(f"Positive Prompt:\n{positive_prompt}\n\nNegative Prompt:\n{negative_prompt}")

                    # Adjust the Backdrop node's size and position
                    read_node.setXpos(100)
                    read_node.setYpos(100)
                    backdrop_node.setXpos(read_node.xpos() - 60)
                    backdrop_node.setYpos(read_node.ypos() - 80)
                    backdrop_node['bdwidth'].setValue(200)
                    backdrop_node['bdheight'].setValue(180)

                    # Place the Read node inside the Backdrop node
                    backdrop_node.setInput(0, read_node)

                    nuke.message(f"Read node created with path:\n{output_path}")
                except ImportError:
                    print("Nuke module not found. Ensure you are running this script within Nuke's environment.")
    except RuntimeError as e:
        print(f"Error: {str(e)}")




class NukeUI(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.directory_path = r"C:\Users\vishr\Downloads\ComfyUI_windows_portable_nvidia\ComfyUI_windows_portable\ComfyUI\models\checkpoints"

        # Set up the layout
        self.setWindowTitle("Nuke UI")
        self.setGeometry(300, 300, 400, 300)
       
        # Layout
        layout = QtWidgets.QVBoxLayout()

        # Drop-down menu
        self.checkpoint_label = QtWidgets.QLabel("Available Files")
        self.checkpoint_dropdown = QtWidgets.QComboBox()
        self.populate_dropdown()

    
        # button for downloading checkpoints
        self.download_button = QtWidgets.QPushButton("Download Checkpoints")
        self.download_button.clicked.connect(self.launch_browser)


        # Text editors
        self.positive_prompt_label = QtWidgets.QLabel("Positive Prompt")
        self.positive_prompt_editor = QtWidgets.QTextEdit()

        self.negative_prompt_label = QtWidgets.QLabel("Negative Prompt")
        self.negative_prompt_editor = QtWidgets.QTextEdit()

        self.image_name_label = QtWidgets.QLabel("Image Name:")
        self.image_name_editor = QtWidgets.QTextEdit()
        self.image_name_editor.setFixedHeight(30)

        # Button
        self.create_read_button = QtWidgets.QPushButton("Run Script")
        self.create_read_button.clicked.connect(self.run_script)

        # Add widgets to layout
        layout.addWidget(self.checkpoint_label)
        layout.addWidget(self.checkpoint_dropdown)
        layout.addWidget(self.download_button)
        layout.addWidget(self.positive_prompt_label)
        layout.addWidget(self.positive_prompt_editor)
        layout.addWidget(self.negative_prompt_label)
        layout.addWidget(self.negative_prompt_editor)
        layout.addWidget(self.image_name_label)
        layout.addWidget(self.image_name_editor)
        layout.addWidget(self.create_read_button)

        # Set layout
        self.setLayout(layout)

    def populate_dropdown(self):
        try:
            files = [f for f in os.listdir(self.directory_path) if os.path.isfile(os.path.join(self.directory_path, f))]
            self.checkpoint_dropdown.addItems(files)
        except FileNotFoundError:
            print(f"Directory not found: {self.directory_path}")
            self.checkpoint_dropdown.addItems([])  # Add no items if directory is not found

    
    def launch_browser(self):
        """Launch the PySide6 browser script."""
        # Path to your PySide6 script
        script_path = r'C:\Users\vishr\Documents\comfy_test\pyside6_browser copy 2.py'
        
        # Path to the Python executable in the PySide6 environment
        python_env_path = r'C:\Users\vishr\Documents\comfy_test\env\Scripts\python.exe'
        
        # Check if the script exists
        if not os.path.exists(script_path):
            QtWidgets.QMessageBox.warning(self, "Error", f"Script not found:\n{script_path}")
            return

        # Check if the Python executable exists
        if not os.path.exists(python_env_path):
            QtWidgets.QMessageBox.warning(self, "Error", f"Python executable not found:\n{python_env_path}")
            return

        try:
            # Launch the external script using subprocess
            subprocess.Popen([python_env_path, script_path], shell=False)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to launch browser:\n{str(e)}")

    def run_script(self):
        # Get user inputs
        checkpoint = self.checkpoint_dropdown.currentText()
        positive_prompt = self.positive_prompt_editor.toPlainText()
        negative_prompt = self.negative_prompt_editor.toPlainText()
        save_image_name = self.image_name_editor.toPlainText()
        
        if not positive_prompt:
            print('Please enter a positive prompt before running the script.')
            return
        
        # Print selected checkpoint and prompts for debugging
        print(f'Selected Checkpoint: {checkpoint}')
        print(f'Positive Prompt: {positive_prompt}')
        print(f'Negative Prompt: {negative_prompt}')
        print(f'Negative Prompt: {save_image_name}')

        try:
            run_image_script(checkpoint, positive_prompt, negative_prompt,save_image_name)
            print('Script executed successfully.')
        
        except Exception as e:
            print(f'An error occurred:\n{str(e)}')

def show_nuke_ui():
    # Create and show the UI
    global ui
    try:
        ui.close()  # Close the UI if it's already open
    except:
        pass

    ui = NukeUI()
    ui.show()
