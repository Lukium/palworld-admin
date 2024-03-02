<h1 align="center" >Palworld A.D.M.I.N.</h1>
<p align="center" >(Automated Deployment, Management & Installation Nexus)

[![PyPI version](https://badge.fury.io/py/palworld_admin.svg)](https://badge.fury.io/py/palworld_admin)


  <image src="https://github.com/Lukium/palworld-admin/assets/99280463/55453c83-f0c4-44e1-b841-b15305243fe3"></image>
  <image src="https://github.com/Lukium/palworld-admin/assets/99280463/adf12f14-ae2a-4191-bd04-b86b4e7f8fd5"></image>
</p>

## **Getting Started:**
1. Choose a version:<br>
  A. palworld-admin.exe and palworld-admin-console.exe are bigger (because they include an Electron App). **While in development, I recommend using the -console version as it helps with troubleshooting**<br>
  B. palworld-admin-no-ui.exe (Windows) and palworld-admin-linux (Linux) are smaller and only run the webserver, which can be accessed via your browser on port 8210<br>
2. Download the app, **on the machine the server will be run on, matching the Operating System** (Download one of the .exe on windows, and the -linux if running on linux)
3. If on windows, **ensure that the app is not in any subdirectory of `c:\users`** otherwise the SteamCMD installtion will fail. I recommend something like `c:\Palworld-Dedicated-Server` or something similar. The directory should be empty at this point.
4. Run the application
5. Click on ![image](https://github.com/Lukium/palworld-admin/assets/99280463/b7c2e86c-03c0-4ca2-8955-e1afe3cc9741)
 to Install a clean version of the dedicated server. Please wait for it to complete the operation (It will download/install SteamCMD and then download Palworld Dedicated Server)
6. If you have an existing server that you want to transfer the data in, click on ![image](https://github.com/Lukium/palworld-admin/assets/99280463/7bdc6228-5ce6-4793-9bbc-a39cb0c4c73d)
, then navigate into the /Saved directory of the existing server and click on upload. This will import the existing server data into Palworld Admin.
7. For security, Palworld Admin will not launch the server unless the admin password is at least 8 characters long. This can be changed by click on ![image](https://github.com/Lukium/palworld-admin/assets/99280463/03474254-3e91-4ba6-8cc3-12bb506cfc76), then setting the password field next to RCONEnabled, then clicking on ![image](https://github.com/Lukium/palworld-admin/assets/99280463/5abf91a8-64e8-43c8-9da7-f0ba80cbf255) to save your settings. **Note, this screen is where you can access all other server settings as well.** With everything set, you can now return to the main screen by clicking on ![image](https://github.com/Lukium/palworld-admin/assets/99280463/343a2d26-e1d5-4a93-83dd-b80d197bd9b0).
8. You should now be able to start your server by clicking on ![image](https://github.com/Lukium/palworld-admin/assets/99280463/d13841d2-5268-4c1f-87ea-92fdc95020d6).
9. To use RCON Features, enter the Server IP/Port/RCON Password on the top of the main window and click on ![image](https://github.com/Lukium/palworld-admin/assets/99280463/a54d69dc-17fe-4542-9ee6-c2c86fcb898a).<br>
**Note:** when managing the server locally (either on same machine or same LAN) use the Local IP displayed on the top of the settings window. When managing the server remotely (over the internet) enter the Public IP, and ensure that port forwarding has been done on port 8210.

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
