const { app, BrowserWindow, Tray, Menu } = require('electron');
const path = require('path');

app.commandLine.appendSwitch('log-level', '3');

const originalConsoleLog = console.log;
console.log = (...args) => {
    if (args[0].includes('[DSH]')) {
        return; // Suppress specific logs
    }
    originalConsoleLog.apply(console, args);
};

let flaskProcess;
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

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 760,
        height: 875,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
        },
        minWidth: 760,
        minHeight: 875,
        autoHideMenuBar: true,
        icon: path.join(__dirname, 'assets', 'icon.ico'),
    });

    mainWindow.loadURL('http://localhost:8210');

    mainWindow.on('close', (event) => {
        if (!app.isQuitting) {
            event.preventDefault();
            mainWindow.hide();
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

    app.on('ready', createWindow);

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
    const http = require('http');
    const options = {
        hostname: '127.0.0.1',
        port: 8210,
        path: '/shutdown',
        method: 'POST',
    };
    const req = http.request(options, (res) => {
        console.log(`statusCode: ${res.statusCode}`);
    });
    req.on('error', (error) => {
        console.error(error);
    });
    req.end();    
    app.isQuitting = true;
});
