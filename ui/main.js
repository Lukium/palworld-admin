const { app, globalShortcut, BrowserWindow, Tray, Menu, Notification } = require('electron');
const path = require('path');

// app.disableHardwareAcceleration(); // Disable hardware acceleration to fix some rendering issues
app.commandLine.appendSwitch('log-level', '3');

if (process.platform === 'win32')
{
    app.setAppUserModelId(app.name);
}

const originalConsoleLog = console.log;
console.log = (...args) => {
    if (args[0].includes('[DSH]')) {
        return; // Suppress specific logs
    }
    originalConsoleLog.apply(console, args);
};

let tray = null;
let mainWindow = null;

function createTray() {
    tray = new Tray(path.join(__dirname, 'assets', 'icon.ico'));
    const contextMenu = Menu.buildFromTemplate([
        { label: 'Show', click: () => { if (mainWindow) mainWindow.show(); } },
        { label: 'Quit', click: () => { app.isQuitting = true; app.quit(); } }
    ]);
    tray.setToolTip('Palworld ADMIN');
    tray.setContextMenu(contextMenu);

    tray.on('click', () => {
        if (mainWindow) mainWindow.show();
    });
}

async function checkZoom() {
    try {
        const zoomLevel = await mainWindow.webContents.getZoomLevel();
        // console.log(`Current zoom level is: ${zoomLevel}`);
        // Perform action based on the zoom level if necessary
        // make the zoom level -1 based on the current zoom level
        //if (zoomLevel !== -1) {
        //    mainWindow.webContents.setZoomLevel(-1);
        //}       

        // const newZoomLevel = await mainWindow.webContents.getZoomLevel();
        // console.log(`New zoom level is: ${newZoomLevel}`);
    } catch (error) {
        console.error('Error getting zoom level:', error);
    }
}

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 900,
        height: 875,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
        },
        minWidth: 900,
        minHeight: 875,
        autoHideMenuBar: true,
        icon: path.join(__dirname, 'assets', 'icon.ico'),
        title: 'Palworld ADMIN',
        backgroundColor: "#212529",
        show: false,        
    });

    mainWindow.setMenu(null);

    const portArgIndex = process.argv.findIndex(arg => arg.startsWith('--port='));
    const port = portArgIndex !== -1 ? process.argv[portArgIndex].split('=')[1] : 8210;

    mainWindow.loadURL(`http://localhost:${port}`);

    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
    });

    mainWindow.webContents.on('did-finish-load', () => {
        checkZoom();
      });

    mainWindow.on('close', (event) => {
        if (!app.isQuitting) {
            event.preventDefault();
            mainWindow.hide();

            // Check if notifications are supported on the user's system
            if (Notification.isSupported()) {
                const notification = new Notification({
                    title: '',
                    body: 'Palworld ADMIN is still running. You can find it in your system tray.',
                    icon: path.join(__dirname, 'assets', 'icon.ico')
                });

                notification.show();
            }
        }
        return false;
    });

    createTray();
}

const gotTheLock = app.requestSingleInstanceLock();

if (!gotTheLock) {
    app.quit();
} else {
    app.on('second-instance', (event, commandLine, workingDirectory) => {
        if (mainWindow) {
            if (mainWindow.isMinimized()) mainWindow.restore();
            mainWindow.focus();
        }
    });

    app.on('ready', () => {
        createWindow();
        // Register a 'CommandOrControl+Shift+I' shortcut listener.
        const ret = globalShortcut.register('CommandOrControl+Shift+I', () => {
            if (mainWindow.isFocused()) {
                const isDevToolsOpened = mainWindow.webContents.isDevToolsOpened();
                if (isDevToolsOpened) {
                    mainWindow.webContents.closeDevTools();
                } else {
                    mainWindow.webContents.openDevTools();
                }
            }
        });

        // Register a 'CommandOrControl+R' shortcut listener.
        const ret2 = globalShortcut.register('CommandOrControl+R', () => {
            if (mainWindow.isFocused()) {
                mainWindow.reload();
            }
        });

        // Check if the shortcut is registered.
        if (mainWindow) {
            mainWindow.webContents.executeJavaScript(
                `console.log('Ctrl+Shift+I shortcut registration status: ${ret}')`
              );
            mainWindow.webContents.executeJavaScript(
              `console.log('Ctrl+R shortcut registration status: ${ret2}')`
            );            
        }
    });

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        } else {
            mainWindow.show();
        }
    });
}

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('before-quit', () => {
    // Post to /shutdown to shutdown the server
    // const http = require('http');
    // const options = {
    //     hostname: '127.0.0.1',
    //     port: 8210,
    //     path: '/shutdown',
    //     method: 'POST',
    // };
    // const req = http.request(options, (res) => {
    //     console.log(`statusCode: ${res.statusCode}`);
    // });
    // req.on('error', (error) => {
    //     console.error(error);
    // });
    // req.end();    
    app.isQuitting = true;
});
