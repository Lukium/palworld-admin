<h1 align="center" >Palworld A.D.M.I.N.</h1>
<p align="center" >(Automated Deployment, Management & Installation Nexus)

[![PyPI version](https://badge.fury.io/py/palworld_admin.svg)](https://badge.fury.io/py/palworld_admin)


  <image src="https://github.com/Lukium/palworld-admin/assets/99280463/55453c83-f0c4-44e1-b841-b15305243fe3"></image>
  <image src="https://github.com/Lukium/palworld-admin/assets/99280463/adf12f14-ae2a-4191-bd04-b86b4e7f8fd5"></image>
</p>

## Feature Roadmap
<details open>
  <summary><b>Server Manager:<b></summary>
<details open>
  <summary>🟢 1-Click Installer</summary>
- 🟢 Windows<br>
- 🟢 Linux  
</details>
<details open>
  <summary>🟢 1-Click Launcher</summary>
- 🟢 Windows<br>
- 🟢 Linux<br>
</details>
<details open>
  <summary>🟢 Data Backup & Restore</summary>
- 🟢 Manually Backup Server Data<br>
- 🟢 Automatically Backup Server Data<br>
- 🟢 AutoPrune Server Data (by quantity)<br>
- 🟢 Restore Server Data from Backup<br>
</details>
<details open>
  <summary>🟢 Server Performance Monitoring</summary>
- 🟢 Server CPU Usage Monitoring<br>
- 🟢 Server RAM Usage Monitoring
</details>
<details open>
  <summary>🟢 Server Auto Restart</summary>
- 🟢 On Unexpected Server Shutdown<br>
- 🟢 RAM Utilization Based
</details>
</details>

<details open>
  <summary>🟢 RCON Client:</summary>
- 🟢 Connect<br>
- 🟢 Broadcast Message (Multi Word working)<br>
- 🟢 List Players<br>
- 🟢 View SteamID/UID<br>
- 🟢 Kick Players<br>
- 🟢 Ban Players<br>
- 🟢 Save Game<br>
- 🟢 Shutdown Gracefully
</details>

<details open>
  <summary>🟢 Server Settings Manager:</summary>
  <details open>
    <summary>🟢 Generate Settings:</summary>
    - 🟢 PalWorldSettings.ini<br>
    - 🟢 WorldOption.sav
  </details>
  <details open>
    <summary>🟢 Read/Write Directly to Server:</summary>
  - 🟢 Read settings directly from server<br>
  - 🟢 Write settings directly to server<br>
  </details>
</details>

<details open>
  <summary>🟡Beyond RCON</summary>
- ⚪ Whitelist Player<br>
- ⚪ Whitelist Mode (Only allow whitelisted players to join server)<br>
- ⚪ Unban Player<br>
- ⚪ Broadcast player joins in server<br>
- ⚪ Create RCON Log<br>
- 🟢 display HEX UID for easy Save Identification
</details>

## **Installation:**
- Simply download the binary that matches your OS and run it.
- I recommend creating something like c:\Palworld Server, or c:\Palworld-Admin, or something simple like this
- **IMPORTANT:** DO NOT RUN IT FROM YOUR DESKTOP, OR ANYTHING LIKE MY DOCUMENTS OR DOWNLOADS (DIRECTORIES THAT CAN BE SYNCED BY ONE DRIVE).<br>
This will cause the Dedicated Server Install to fail.

## **To access the Remote Server Manager:**
- Run the binary on your host using the -r -mp flags:<br>
  For Windows: `palworld-admin.exe -r -mp [managementpassword]` _Also works with -console version_<br>
  For Linux: `palworld-admin -r -mp [managementpassword]` _Make sure to `chmod + x` first_
- Make sure port 8210 is open and forwarded
- Access it with your browser of choice by navigating to http://[HOSTIP]:8210

**Important:**
The remote manager does not have RCON built in. You still want to use the windows version to access the server managed in Linux via RCON

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
- Go to Local Server Manager in the main menu
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


## Troubleshooting:
### 1. Failure to Install/Launch Server:
The most likely cause for this is the user running Palworld A.D.M.I.N. from the desktop, a folder in the desktop, or a folder in a windows directory that's "syncable" like Documents / Downloads / etc.<br>
Instead I recommend creating a directory like c:\Palworld-Admin or c:\Palworld Server.


### 2. Undefined values in Server Manager after importing server (See screenshot below):
- This might happen if you have changed the default formatting on the PalWorldSettings.ini file. Palworld A.D.M.I.N. expects the file to be in its original formatting. The values can all be changed, but the formatting must remain intact (All options in a single line)<br>
- Another possibility is that there are commas inside values surrounded by "" like your Server Name or Description. At this time this is a limitation of the app that I intend to eventually remove. So for now, no commas in the values.
![image](https://github.com/Lukium/palworld-admin/assets/99280463/ca9facea-c3c4-4550-b828-8db4810c8eab)


### 3. Webview2 Runtime Requirement:
If you are running a non-standard version of windows (for example, Remote/Virtual Environment, Windows Server) you will likely need to install the Webview2 runtime from Microsoft, which can be found [here](https://go.microsoft.com/fwlink/p/?LinkId=2124703). More information - [here](https://developer.microsoft.com/en-us/microsoft-edge/webview2/?form=MA13LH#download)
You will know this is the case if upon opening the app, it looks like either of the following screenshots:<br>
![image](https://github.com/Lukium/palworld-servertools/assets/99280463/582eac35-40f5-4a17-abec-55da4389a356)
![image](https://github.com/Lukium/palworld-servertools/assets/99280463/2f0d585e-af54-4236-9426-7cf36fee7c90)


### 4. Crushed / Squeezed UI
If the UI looks like the screenshot below, please increase the resolution of your display. If using a remote connection where you can't change the Resolution settings, you can usually do it from the Remote Client Options in the App that you use to connect (before actually making the Remote Desktop Connection):
![image](https://github.com/Lukium/palworld-admin/assets/99280463/59a62462-498e-4795-a575-5d803a5afef1)


Credits:

- https://github.com/cheahjs/palworld-save-tools (Expanded and Modified)

- https://github.com/itzg/rcon-cli (Expanded, Modified, Translated to Python)
