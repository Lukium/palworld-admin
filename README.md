# Palworld Dedicated Server Tools

## How to run directly from the code:
- Install python, at least 3.11
- Install poetry `pip install poetry` make sure you add it to your PATH
- Download the code to a directory
- From that directory run `poetry install`
- Then run `poetry run python main.py`
- Profit

## How to transition from an existing server:
- **MAKE A BACKUP**
- Download the newest version of the app
- Got to Local Server Manager in the main menu
- Click `Install | Update` > `Confirm` > Wait for it to finish
- Go to your backup and copy the directory:
`steamapps/common/PalServer/Pal/Saved` **FROM** your backup and overwrite that same directory inside the steamcmd that my app creates
- Restart the app > Local Server Manager
- You should now see the existing options of your server
- Modify them as needed, including adding an Admin Password (this is the RCON password as well)
- Click the button to update settings (This will save the changes)
- Click Start Server, take note of the Local IP / RCON port / Admin Pass
- Switch to RCON window
- Enter the Local IP / RCON port / Admin
- Click Connect
You should now be connected to the server via RCON

![image](https://github.com/Lukium/palworld-servertools/assets/99280463/75f144d2-e3d7-413b-a357-c25e38488421)
![image](https://github.com/Lukium/palworld-servertools/assets/99280463/502ebcde-422b-444b-8574-d360b5e3c577)
![image](https://github.com/Lukium/palworld-servertools/assets/99280463/be2c08c7-6c8c-4324-97fc-30732157f893)

Credits:

- https://github.com/cheahjs/palworld-save-tools (Expanded and Modified)

- https://github.com/itzg/rcon-cli (Expanded, Modified, Translated to Python)
