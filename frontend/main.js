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
    // Get path to the starter script
    const isPackaged = app.isPackaged;
    let scriptPath;
    
    if (isPackaged) {
      // In packaged app, the Python executable is bundled
      scriptPath = path.join(process.resourcesPath, 'start_backend.py');
    } else {
      // In development, use the script from the project directory
      scriptPath = path.join(__dirname, '..', 'start_backend.py');
    }

    console.log(`Starting backend with ${scriptPath} on port ${backendPort}`);
    
    // Make the starter script executable
    try {
      fs.chmodSync(scriptPath, 0o755);
    } catch (err) {
      console.warn(`Failed to make script executable: ${err.message}`);
    }

    // Try different Python executable names (python3 is common on macOS)
    const pythonExecutables = ['python3', 'python', 'py', './start_backend.py'];
    let executableIndex = 0;
    
    const tryNextExecutable = () => {
      if (executableIndex >= pythonExecutables.length) {
        return reject(new Error('Could not find Python executable. Please ensure Python 3 is installed and in your PATH.'));
      }
      
      const executable = pythonExecutables[executableIndex];
      console.log(`Trying executable: ${executable}`);
      
      // Prepare command arguments based on executable
      let args = [];
      if (executable === './start_backend.py') {
        // Direct execution of the starter script
        args = [backendPort.toString()];
        // Launch the backend process with the script directly
        backendProcess = spawn(executable, args, {
          stdio: 'pipe',
          cwd: path.dirname(scriptPath)
        });
      } else {
        // Python interpreter execution
        args = [scriptPath, backendPort.toString()];
        // Launch the backend process
        backendProcess = spawn(executable, args, {
          stdio: 'pipe'
        });
      }
      
      backendProcess.on('error', (err) => {
        console.error(`Failed to start with ${executable}:`, err);
        executableIndex++;
        backendProcess = null;
        tryNextExecutable();
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
        // If process closed without becoming ready and it's not an error we already handled
        if (!backendReady && code !== null) {
          console.log(`Backend process with ${executable} exited with code ${code}`);
          executableIndex++;
          backendProcess = null;
          tryNextExecutable();
        } else {
          console.log(`Backend process exited with code ${code}`);
          backendProcess = null;
        }
      });
    };
    
    // Start trying executables
    tryNextExecutable();

    // Set a timeout for startup
    setTimeout(() => {
      if (!backendReady) {
        console.error('Backend startup timed out');
        if (backendProcess) {
          // If process is still running but not sending the expected message,
          // let's try connecting anyway
          console.log('Backend process is running but not sending ready signal. Attempting to connect anyway...');
          backendReady = true;
          resolve();
        } else {
          reject(new Error('Backend startup timed out'));
        }
      }
    }, 30000);
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
