<h1 align="center" >Palworld A.D.M.I.N.</h1>
<p align="center" >(Automated Deployment, Management & Installation Nexus)


[<image src="https://img.shields.io/github/v/release/Lukium/palworld-admin?style=for-the-badge&label=github"></image>](https://github.com/Lukium/palworld-admin/releases/latest) ![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/lukium/palworld-admin/total?style=for-the-badge) ![GitHub commit activity](https://img.shields.io/github/commit-activity/m/lukium/palworld-admin?style=for-the-badge) <br>
[<image src="https://img.shields.io/pypi/v/palworld-admin?style=for-the-badge"></image>](https://pypi.org/project/palworld_admin/) ![PyPI - Downloads](https://img.shields.io/pypi/dm/palworld-admin?style=for-the-badge) ![PyPI - Format](https://img.shields.io/pypi/format/palworld-admin?style=for-the-badge) <br>
[<image src="https://img.shields.io/docker/v/lukium/palworld-admin-wine/latest?style=for-the-badge&logo=docker&label=docker-wine"></image>](https://hub.docker.com/repository/docker/lukium/palworld-admin-wine/general) ![Docker Pulls](https://img.shields.io/docker/pulls/lukium/palworld-admin-wine?style=for-the-badge) <br>
[<image src="https://img.shields.io/discord/629066705057873922?style=for-the-badge&label=discord"></image>](https://discord.gg/lukium)






  <image src="https://github.com/Lukium/palworld-admin/assets/99280463/55453c83-f0c4-44e1-b841-b15305243fe3"></image>
  <image src="https://github.com/Lukium/palworld-admin/assets/99280463/adf12f14-ae2a-4191-bd04-b86b4e7f8fd5"></image>
</p>

## **Getting Started:**
### Choose a Version:
**Choose a version that matches the Operating System of the machine the Dedicated Server will be run on, not the machine you will manage the server from.**<br>
For Windows, choose a .exe, for linux use palworld-admin-linux
#### Windows:
Compatibility: Windows 10+ / Windows Server 2019+ (Success has been reported on Windows Server 2016 but not recommended)
- palworld-admin.exe:
  Webserver + Electron UI - Clean, simple experience
- palworld-admin-console.exe
  WebServer + Electron UI + Console - Same as above plus a console, helpful for troubleshooting, if you need help, you must be using this version to provide troubleshooting information.
- palworld-admin-no-ui.exe
  Webserver Only - Lightweight, use this version if you would like to use your browser to manage the server by visiting http://127.0.0.1:8210 (or the server's IP if managing a remote server)
#### Linux:
Compatibility: Tested on 23.04+, should work on 22.04+ as long as you have Python3.11+ installed
- palworld-admin-linux
  Webserver Only - Lightweight, use this version if you would like to use your browser to manage the server by visiting http://127.0.0.1:8210 (or the server's IP if managing a remote server)

### Installation:
1. Choose version (See above)
2. Create an empty directory. This is where the application will be run from. Recommended:<br>
`c:\Palworld-Dedicated-Server` (Windows)<br>
`$HOME/Palworld-Dedicated-Server` (Linux)<br>
**Note for Windows Users:**<br>
The directory **MUST NOT BE IN** a `Known Folder`, including but not limited to, `My Documents`, `Downloads`, `Desktop` otherwise the SteamCMD installtion will fail.
3. Download the latest version from [Releases](https://github.com/Lukium/palworld-admin/releases/latest) and place it in the directory you created in step 2
4. Run the application<br>
**Note for Linux as well as users intending to manage a remote server:**<br>
- Make sure that TCP port 8210 is forwarded to the machine the server will be running on.
- For securty, **YOU MUST RUN THE APPLICATION** with `-r -mp [management-password]`.
This will make it so that in order to access the server a `[management-password]` must be entered.<br>If you do not this, anyone can take full control of your server by accessing it's IP address on port 8210 with any browser.
5. Click on ![image](https://github.com/Lukium/palworld-admin/assets/99280463/b7c2e86c-03c0-4ca2-8955-e1afe3cc9741) to Install a clean version of the dedicated server. Please wait for it to complete the operation, which does the following:<br>
- Download and Install SteamCMD
- Download and Install Palworld Dedicated Server
- Create necessary symlinks for SteamCMD (Linux Only)
- Initial 5 second run of the server to create default files and paths
- Copying the default PalWorldSettings.ini into the Config Directory
6. (Optional) If you have an existing server that you want to transfer the data in, click on ![image](https://github.com/Lukium/palworld-admin/assets/99280463/7bdc6228-5ce6-4793-9bbc-a39cb0c4c73d) then navigate into the /Saved directory of the existing server and click on upload. This will import the existing server data into Palworld Admin.
7. For security, Palworld Admin will not launch the server unless the admin password is at least 8 characters long. This can be changed by click on ![image](https://github.com/Lukium/palworld-admin/assets/99280463/03474254-3e91-4ba6-8cc3-12bb506cfc76), then setting the password field next to RCONEnabled, then clicking on ![image](https://github.com/Lukium/palworld-admin/assets/99280463/5abf91a8-64e8-43c8-9da7-f0ba80cbf255) to save your settings. **Note, this screen is where you can access all other server settings as well.** With everything set, you can now return to the main screen by clicking on ![image](https://github.com/Lukium/palworld-admin/assets/99280463/343a2d26-e1d5-4a93-83dd-b80d197bd9b0).
8. You should now be able to start your server by clicking on ![image](https://github.com/Lukium/palworld-admin/assets/99280463/d13841d2-5268-4c1f-87ea-92fdc95020d6).
9. To use RCON Features, enter the Server IP/Port/RCON Password on the top of the main window and click on ![image](https://github.com/Lukium/palworld-admin/assets/99280463/a54d69dc-17fe-4542-9ee6-c2c86fcb898a).<br>
**Note:** when managing the server locally (either on same machine or same LAN) use the Local IP displayed on the top of the settings window. When managing the server remotely (over the internet) enter the Public IP, and ensure that port forwarding has been done on port 8210. <br>
10. If you enable "SteamAuth Required", then players will need to visit http://[palworldadminip]:8210/steam-auth and sign in with their Steam Account before they are able to connect to the server without being kicked. "Enfoce SteamAuth IP" Requires Palguard, and will make sure that only a player whose IP matches the IP used to process the steamAuth can connect to the server.

## Running Docker Image:
### IMPORTANT:
If you mount the directories as explained below, they must be owned by UID:GID 1001:1001 on the host, otherwise you will have permission errors.
If your distro doesn't already have a 1001:1001 user (you can check by running `sudo cat /etc/passwd`), then you can create the user and set the user perms by running the following commands:
```bash
sudo useradd -u 1001 -g 1001 [username]
sudo chown [username]:[username] /path/to/dir
```

Simply run (if using Docker, or use any alternative you like such as Docker Compose or Kubernetes:
```bash
docker run \
	-e MANAGEMENT_PASSWORD="[management-password]" \
	-p [desired palworld-admin port]:8210/tcp \
	-p [desired game port]:[desired game port]/udp \
	-p [desired RCON port]:[desired RCON port]/tcp \
	-p [desired query port]:[desired query port]/udp \
	-v [location on host to mount palworld-admin directory]:/home/lukium/palworld-admin/ \
	-v [location on host to mount Palworld Dedicated Server directory]:/home/lukium/.wine/drive_c/steamcmd/ \
	--name [desired container name] \
	lukium/palworld-admin-wine:latest
```
Docker Compose:
```yaml
# docker-compose.yml

version: '3.8'
services:
  app:
    container_name: ${CONTAINER_NAME}
    image: 'lukium/palworld-admin-wine:${CONTAINER_VERSION}'
    restart: unless-stopped
    environment:
      MANAGEMENT_PASSWORD: ${MANAGEMENT_PASSWORD}
    ports:
      - '${ADMIN_PORT}:8210/tcp'
      - '${GAME_PORT}:${GAME_PORT}/udp'
      - '${RCON_PORT}:${RCON_PORT}/tcp'
      - '${QUERY_PORT}:${QUERY_PORT}/udp'
    volumes:
      - ./palworld-admin:/home/lukium/palworld-admin/
      - ./PalServer:/home/lukium/.wine/drive_c/steamcmd/

# .env

CONTAINER_NAME=Palworld Server
CONTAINER_VERSION=latest
MANAGEMENT_PASSWORD=changeme
ADMIN_PORT=8210
GAME_PORT=8211
RCON_PORT=25575
QUERY_PORT=27015
```
For example:
```bash
docker run \
	-e MANAGEMENT_PASSWORD="test123" \
	-p 8210:8210/tcp \
	-p 8211:8211/udp \
	-p 25575:25575/tcp \
	-p 25575:25575/udp \
	-p 27015:27015/tcp \
	-p 27015:27015/udp \
	-v $HOME/palworld-admin/app/:/home/lukium/palworld-admin/ \
	-v $HOME/palworld-admin/server/:/home/lukium/.wine/drive_c/steamcmd/ \
	--name palworld-admin-wine \
	lukium/palworld-admin-wine:latest
```

## How to run directly from the code:
- Install python, at least 3.11
- Install poetry `pip install poetry` make sure you add it to your PATH
- Optional but recommended: Set poetry to place the venv in the project directory by using the command `poetry config virtualenvs.in-project true`
- Git clone the repo
- From the palworld-admin directory run `poetry install`
- Ensure that in `./palworld_admin/settings.py` that `self.no_ui: bool = False` (In order to keep the repo clean, it does not contain the Electron UI executables so if running from code you must run no-ui)
- Run `poetry run python ./palworld_admin/main.py`
- Access the application via the browser on port 8210 (e.g. http://127.0.0.1:8210)

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

### 2. Unhandled exception in script with `OSError: [WinError 10048] Only one usage of each socket address (protocol/network address/port) is normally permitted`
(See screenshot below) This means that the webserver is already running (maybe the application didn't fully close before). Check your task manager and close palworld-admin manually before trying to restart the application. <br>
![image](https://github.com/Lukium/palworld-admin/assets/99280463/2b06d249-874a-41d9-a602-e20be741340a)

### 3. Unhandled exception in script with `sqlite3.OperationalError`
(See screenshot below) This means that the application database need to be upgraded. Re-run the application with -mdb flag, e.g., `palworld-admin.exe -mdb` and this should upgrade the database to current.
![image](https://github.com/Lukium/palworld-admin/assets/99280463/bdd32178-24a7-4920-aa27-d35d10990061)

### 4. I set a RAM Auto-Restart to 16GB, my task manager says that the server is using ~16100mb, but the server has not restarted, how come?
1 GB = 1024 MB. This means that the server will not restart at 16000MB, because 16000 MB is not 16GB. 16 GB = 16384 MB. Also, The logic is that the server must exceed the limit 3 times a row (to prevent unecessary restarts should it just be a random spike). You should see notifications in the application saying that it has been triggered 1/3, 2/3 and 3/3, before a restart.

### 5. Repeated `Error: list index out of range` / I can't kick a player in my server
This typically results from someone in your playerlist having a name that breaks RCON. Unfortunately, Palworld's RCON is very rudimentary and names with non-ASCII characters messes with it. Another symptom is being unable to kick/ban a player via RCON. Tell your players to use names with ASCII characters until the ingame-RCON is improved upon.


Credits:

- https://github.com/cheahjs/palworld-save-tools (Expanded and Modified)

- https://github.com/itzg/rcon-cli (Expanded, Modified, Translated to Python)
