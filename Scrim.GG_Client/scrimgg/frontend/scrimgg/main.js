const { app, BrowserWindow } = require('electron');
const { spawn } = require('child_process');
const path = require('path');

let pythonProcess;

function createWindow() {
  // Create the browser window.
  const win = new BrowserWindow({
    width: 1000,
    height: 700,
    // frame: false,
    webPreferences: {
      nodeIntegration: true,
      // preload: path.join(__dirname, 'preload.js'),
    },
    // autoHideMenuBar: true,
  });
  win.loadURL('http://localhost:3000');
  }

  function startPythonBackend() {
    const backendPath = path.join(__dirname, '..', '..', 'backend', 'bootstrap.py');
    try {
        pythonProcess = spawn('python', [backendPath], {
            env: { ...process.env, PYTHONUNBUFFERED: '1' } // Unbuffered output
        });

        pythonProcess.stdout.on('data', (data) => {
            console.log(`Python stdout: ${data.toString().trim()}`);
        });

        pythonProcess.stderr.on('data', (data) => {
            console.error(`Python stderr: ${data.toString().trim()}`);
        });

        pythonProcess.on('close', (code) => {
            console.log(`Python process exited with code ${code}`);
        });
    } catch (err) {
        console.error('Error spawning Python process:', err);
    }
}
  
  app.whenReady().then(() => {
    startPythonBackend(); 
    createWindow();
  });

  app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
      // Close Python backend process when Electron app is closed
      if (pythonProcess) {
        pythonProcess.kill();
      }
      app.quit();
    }
  });

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});


