# Video-Link
https://www.linkedin.com/posts/gunda-pratap_nuke-vfx-generativeai-activity-7282138363669725184-3VUL?utm_source=share&utm_medium=member_desktop&rcm=ACoAABOSQCsBCEJyn-YU9zw7k26TQIRfPhs248A
# show-manager
Creates shot list and folder structure. launches nuke houdini etc applications.

## What is a show manager
Show manager is to create and manage shows and shots under that show. We can simply import Excel data to create show and shot list. We can set shot resolution, frame range and comments like what is the task in that shot etc. We can also create folder structure for each shot automatically. All this data we can later use when we work on shots.
- **UI of show manager**
![Excel sheet Example](./resources/Show_manager_SS.jpg)

## What is a project launcher
Project launcher is to use the data we added in show manager. we can launch softwares like nuke, houdini, substance with the feeded settings automatically. For eg. it will launch nuke with pre defined settings like resolution frame range and nuke templete to work.
- **UI of project launcher**
![Excel sheet Example](./resources/Project_launcher_SS.jpg)

## How to Use?

1. Clone this repo:
    ```bash
    git clone https://github.com/pratap-gunda/show-manager.git
    ```
2. Get the dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3. Copy comfiui code to .nuke:
   download and paste 'comfy_nuke_prompt_main.py' to your .nuke folder.

4. Copy menu.py code from this repo to your menu.py in .nuke folder.
5. download and paste custom_tools folder in .nuke folder.
 
6. Launch the manager:
    ```bash
    python ./show_manager.py
    ```
4. Pick a folder, show, shot, resolution etc.
5. You can also use an excel file with multiple `SHOW`, `SHOT`, `RESOLUTION`, `COMMENTS` columns.
6. Below is the example Excel sheet columns.
![Excel sheet Example](./resources/Excel_example.jpg)
4. To launch project launcher:
    ```bash
    python ./project_launcher.py
    ```
