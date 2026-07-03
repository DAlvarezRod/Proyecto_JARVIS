const { app, BrowserWindow } = require('electron');

const VITE_URL = 'http://127.0.0.1:5173';
let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1100,
    height: 800,
    minWidth: 600,
    minHeight: 400,
    title: 'Illo',
    autoHideMenuBar: true,
    backgroundColor: '#0a0a12',
    show: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  mainWindow.loadURL(VITE_URL);

  mainWindow.once('ready-to-show', function () {
    mainWindow.show();
  });

  mainWindow.webContents.on('did-fail-load', function () {
    setTimeout(function () {
      mainWindow.loadURL(VITE_URL);
    }, 2000);
  });

  mainWindow.on('closed', function () {
    mainWindow = null;
  });
}

app.whenReady().then(createWindow);

app.on('window-all-closed', function () {
  app.quit();
});

app.on('activate', function () {
  if (mainWindow === null) createWindow();
});
