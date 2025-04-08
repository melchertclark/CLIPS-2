const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');
const axios = require('axios');

// Keep a global reference of the window object to avoid garbage collection
let mainWindow;

// Backend process reference
let backendProcess = null;
let backendPort = 3000; // Default initial port
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

  // When window is ready, send the backend port
  mainWindow.webContents.on('did-finish-load', () => {
    console.log(`Sending backend port ${backendPort} to renderer process`);
    mainWindow.webContents.send('update-backend-port', backendPort);
  });

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// Start the Python backend server
async function startBackend() {
  return new Promise((resolve, reject) => {
    // Skip starting backend if we're in direct mode (backend started externally)
    const skipBackendStart = process.argv.includes('--external-backend');
    if (skipBackendStart) {
      console.log('Using externally started backend');
      backendReady = true;
      return resolve();
    }
    
    // Get path to the starter script
    const isPackaged = app.isPackaged;
    let scriptPath;
    
    if (isPackaged) {
      // In packaged app, the Python executable is bundled
      scriptPath = path.join(process.resourcesPath, 'backend', 'main.py');
    } else {
      // In development, use the script from the project directory
      scriptPath = path.join(__dirname, '..', 'backend', 'main.py');
    }

    console.log(`Starting backend with ${scriptPath} on port ${backendPort}`);
    
    // Launch the backend process
    backendProcess = spawn('python3', [scriptPath], {
      stdio: 'pipe'
    });
    
    backendProcess.on('error', (err) => {
      console.error(`Failed to start backend:`, err);
      reject(new Error(`Failed to start backend: ${err.message}`));
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

    backendProcess.on('close', (code) => {
      console.log(`Backend process exited with code ${code}`);
      backendProcess = null;
      
      if (!backendReady) {
        reject(new Error(`Backend process exited with code ${code}`));
      }
    });

    // Set a timeout for startup
    setTimeout(() => {
      if (!backendReady) {
        console.error('Backend startup timed out');
        if (backendProcess) {
          backendProcess.kill();
          backendProcess = null;
        }
        reject(new Error('Backend startup timed out'));
      }
    }, 10000);
  });
}

// Read port from backend_port.txt file
function readBackendPortFromFile() {
  try {
    const portFile = path.join(__dirname, '..', 'backend_port.txt');
    
    if (fs.existsSync(portFile)) {
      const port = parseInt(fs.readFileSync(portFile, 'utf8').trim(), 10);
      console.log(`Read backend port ${port} from file`);
      
      if (!isNaN(port) && port > 0) {
        backendPort = port;
        return true;
      }
    }
    
    return false;
  } catch (error) {
    console.error('Error reading backend port file:', error);
    return false;
  }
}

// Check if backend is ready by pinging the API
async function checkBackendReady() {
  try {
    // Try to read port from file first if we're in external mode
    if (process.argv.includes('--external-backend')) {
      readBackendPortFromFile();
    }
    
    console.log(`Checking backend status on port ${backendPort}...`);
    // Explicitly use IPv4 address (127.0.0.1) instead of localhost which might resolve to IPv6
    const response = await axios.get(`http://127.0.0.1:${backendPort}/api/status`);
    return response.status === 200;
  } catch (error) {
    console.error(`Backend check failed on port ${backendPort}:`, error.message);
    return false;
  }
}

// Wait for backend to be ready with polling
async function waitForBackend(maxAttempts = 20, interval = 1000) {
  console.log(`Waiting for backend to be ready...`);
  
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    console.log(`Connection attempt ${attempt + 1}/${maxAttempts}`);
    
    // Always read the port file first on each attempt
    if (process.argv.includes('--external-backend')) {
      const portFileExists = readBackendPortFromFile();
      console.log(`Port file ${portFileExists ? 'found' : 'not found'}, using port ${backendPort}`);
    }
    
    try {
      if (await checkBackendReady()) {
        console.log('Backend is ready!');
        return true;
      }
    } catch (error) {
      console.log(`Connection failed: ${error.message || 'Unknown error'}`);
    }
    
    await new Promise(resolve => setTimeout(resolve, interval));
  }
  
  console.error(`Failed to connect to backend after ${maxAttempts} attempts`);
  return false;
}

// Initialize the app
app.whenReady().then(async () => {
  try {
    console.log("Electron app is ready");
    console.log("Command line arguments:", process.argv);
    
    if (process.argv.includes('--external-backend')) {
      console.log("Using external backend mode");
      // Try to read port from file immediately 
      const portFound = readBackendPortFromFile();
      console.log(`Port file read success: ${portFound}, using port ${backendPort}`);
    } else {
      // Start the backend server
      console.log("Starting internal backend");
      await startBackend();
    }
    
    // Wait for backend to be ready
    console.log("Now waiting for backend to be ready...");
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
