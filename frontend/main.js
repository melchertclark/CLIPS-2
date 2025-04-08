const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');
const axios = require('axios');

// Keep a global reference of the window object to avoid garbage collection
let mainWindow;

// Backend process reference
let backendProcess = null;
let backendPort = 5000;
let backendReady = false;

// Debug mode
const DEBUG = process.argv.includes('--debug');

function createWindow() {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      enableRemoteModule: true,
    },
    title: 'CLIPS - Copywriter\'s Lightweight Iteration Pipeline System',
    icon: path.join(__dirname, 'assets', 'icon.png')
  });

  // Load the index.html file
  mainWindow.loadFile(path.join(__dirname, 'index.html'));

  // Open DevTools in debug mode
  if (DEBUG) {
    mainWindow.webContents.openDevTools();
  }

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// Start the Python backend server
async function startBackend() {
  return new Promise((resolve, reject) => {
    // Determine the path to the Python script
    const isPackaged = app.isPackaged;
    let scriptPath;
    
    if (isPackaged) {
      // In packaged app, the Python executable is bundled
      scriptPath = path.join(process.resourcesPath, 'backend', 'main.py');
    } else {
      // In development, use the script from the project directory
      scriptPath = path.join(__dirname, '..', 'backend', 'main.py');
    }

    console.log(`Starting backend at ${scriptPath} on port ${backendPort}`);

    // Launch the backend process
    backendProcess = spawn('python', [scriptPath, backendPort.toString()], {
      stdio: 'pipe'
    });

    // Handle backend process output
    backendProcess.stdout.on('data', (data) => {
      console.log(`Backend stdout: ${data}`);

      // Check if server is running
      if (data.toString().includes('Running on http://')) {
        backendReady = true;
        resolve();
      }
    });

    backendProcess.stderr.on('data', (data) => {
      console.error(`Backend stderr: ${data}`);
    });

    backendProcess.on('error', (err) => {
      console.error('Failed to start backend process:', err);
      reject(err);
    });

    backendProcess.on('close', (code) => {
      console.log(`Backend process exited with code ${code}`);
      backendProcess = null;
    });

    // Set a timeout for startup
    setTimeout(() => {
      if (!backendReady) {
        console.error('Backend startup timed out');
        reject(new Error('Backend startup timed out'));
      }
    }, 10000);
  });
}

// Check if backend is ready by pinging the API
async function checkBackendReady() {
  try {
    const response = await axios.get(`http://localhost:${backendPort}/api/status`);
    return response.status === 200;
  } catch (error) {
    return false;
  }
}

// Wait for backend to be ready with polling
async function waitForBackend(maxAttempts = 10, interval = 500) {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    if (await checkBackendReady()) {
      return true;
    }
    await new Promise(resolve => setTimeout(resolve, interval));
  }
  return false;
}

// Initialize the app
app.whenReady().then(async () => {
  try {
    // Start the backend server
    await startBackend();
    
    // Wait for backend to be ready
    if (await waitForBackend()) {
      console.log('Backend is ready');
      createWindow();
    } else {
      console.error('Backend failed to start properly');
      dialog.showErrorBox(
        'Backend Error', 
        'Failed to start the backend server. Please check your Python installation and dependencies.'
      );
      app.quit();
    }
  } catch (error) {
    console.error('Error during startup:', error);
    dialog.showErrorBox(
      'Startup Error', 
      `Failed to initialize the application: ${error.message}`
    );
    app.quit();
  }
  
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

// Quit when all windows are closed, except on macOS
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// Clean up the backend process when the app is quitting
app.on('will-quit', () => {
  if (backendProcess) {
    console.log('Terminating backend process...');
    backendProcess.kill();
    backendProcess = null;
  }
});

// IPC handlers
ipcMain.handle('open-file-dialog', async (event, options) => {
  const { filters, properties } = options || {};
  const result = await dialog.showOpenDialog(mainWindow, {
    filters: filters || [],
    properties: properties || ['openFile']
  });
  return result.filePaths;
});

ipcMain.handle('save-file-dialog', async (event, options) => {
  const { filters, defaultPath } = options || {};
  const result = await dialog.showSaveDialog(mainWindow, {
    filters: filters || [],
    defaultPath: defaultPath || ''
  });
  return result.filePath;
});

ipcMain.handle('show-error-dialog', async (event, options) => {
  const { title, message } = options || {};
  dialog.showErrorBox(title || 'Error', message || 'An error occurred');
  return true;
});

ipcMain.handle('open-external-link', async (event, url) => {
  await shell.openExternal(url);
  return true;
});

ipcMain.handle('show-output-folder', async () => {
  const outputPath = path.join(__dirname, '..', 'output');
  await shell.openPath(outputPath);
  return true;
});
