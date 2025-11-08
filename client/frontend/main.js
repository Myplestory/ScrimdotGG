const { app, BrowserWindow, ipcMain } = require('electron');
const { spawn, exec, execSync } = require('child_process');
const path = require('path');
const process = require('process');

let pythonProcess;
let pythonProcessPid;

function createWindow() {
  // Create the browser window.
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    resizable: true,
    frame: false,
    transparent: true, // Make window transparent initially
    opacity: 0, // Start with 0 opacity
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
    autoHideMenuBar: true,
  });
  
  // Handle close app IPC
  ipcMain.on('close-app', () => {
    win.close();
  });

  // Handle minimize window
  ipcMain.on('minimize-window', () => {
    win.minimize();
  });

  // Handle maximize/restore window toggle
  ipcMain.on('maximize-window', () => {
    if (win.isMaximized()) {
      win.unmaximize();
    } else {
      win.maximize();
    }
  });

  // Handle fade in window when React is ready
  ipcMain.on('react-ready', () => {
    console.log('🎬 React is ready, fading in window...');
    // Set opacity to 1 immediately (no animation for now)
    win.setOpacity(1);
  });
  
  win.loadURL('http://localhost:3000');
  
  // Fallback: Make window visible after 3 seconds if React doesn't signal ready
  setTimeout(() => {
    if (win.getOpacity() === 0) {
      console.log('🔄 Fallback: Making window visible after timeout');
      win.setOpacity(1);
    }
    }, 3000);
  }

  function startPythonBackend() {
    const backendPath = path.join(__dirname, '..', 'backend', 'run.py');
    const backendDir = path.join(__dirname, '..', 'backend');
    
    console.log(' Starting Python backend (REFACTORED)...');
    console.log(' Backend directory:', backendDir);
    console.log(' Backend script:', backendPath);
    
  try {
    // Determine Python command based on environment
    const isDev = process.env.NODE_ENV === 'development';
    let pythonCommand, pythonArgs;

    if (isDev) {
      // Development: try to detect pipenv venv dynamically
      try {
        // Ask pipenv for the venv path for the backend directory
        const venvPath = execSync('pipenv --venv', { cwd: backendDir, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
        if (venvPath) {
          const candidate = path.join(venvPath, 'Scripts', 'python.exe');
          try {
            require('fs').accessSync(candidate);
            pythonCommand = candidate;
            pythonArgs = ['run.py'];
            console.log(`✅ [DEV] Resolved pipenv venv Python: ${pythonCommand}`);
          } catch (err) {
            // venv exists but python binary not found where expected
            console.log(`⚠️ [DEV] pipenv venv found but python.exe missing at ${candidate}: ${err.message}`);
            throw err;
          }
        } else {
          throw new Error('pipenv returned empty venv path');
        }
      } catch (err) {
        // Fallback: run via pipenv run ... (requires pipenv on PATH)
        console.log(`❌ [DEV] Could not resolve pipenv venv automatically (${err.message}), falling back to 'pipenv run'`);
        pythonCommand = 'pipenv';
        pythonArgs = ['run', 'python', 'run.py'];
      }
    } else {
      // Production: use system Python or compiled executable
      const compiledExe = path.join(backendDir, 'backend.exe');
      try {
        require('fs').accessSync(compiledExe);
        pythonCommand = compiledExe;
        pythonArgs = [];
        console.log(`✅ [PROD] Using compiled executable: ${pythonCommand}`);
      } catch (e) {
        pythonCommand = 'python';
        pythonArgs = ['run.py'];
        console.log(`✅ [PROD] Using system Python: ${pythonCommand}`);
      }
    }
        
        pythonProcess = spawn(pythonCommand, pythonArgs, {
            cwd: backendDir,
            shell: true,
            env: { ...process.env, PYTHONUNBUFFERED: '1' },
            detached: false  // Keep process attached so it dies with parent
        });

        // Store the PID for cleanup
        pythonProcessPid = pythonProcess.pid;
        console.log(`🔢 Backend process PID: ${pythonProcessPid}`);

        pythonProcess.stdout.on('data', (data) => {
            console.log(`🐍 [Backend] ${data.toString().trim()}`);
        });

        pythonProcess.stderr.on('data', (data) => {
            console.log(`[Backend] ${data.toString().trim()}`);
        });

        pythonProcess.on('close', (code) => {
            console.log(`🔄 [Backend] Process exited with code ${code}`);
            pythonProcessPid = null;
        });

        pythonProcess.on('error', (err) => {
            console.error('💥 [Backend] Failed to start:', err.message);
            console.log('💡 Make sure pipenv is installed and backend dependencies are set up');
        });

        console.log('✅ Python backend process started');
    } catch (err) {
        console.error('💥 Error spawning Python process:', err);
    }
}
  
  app.whenReady().then(() => {
    console.log('🚀 Electron app is ready, cleaning up any existing processes...');
    
    // Kill any existing backend processes before starting new one
    forceKillBackendProcesses();
    
    // Wait a moment for cleanup, then start fresh backend
    setTimeout(() => {
      console.log('🚀 Starting fresh backend...');
      startPythonBackend(); 
      console.log('🚀 Electron app is ready, creating window...');
      createWindow();
    }, 2000); // Wait 2 seconds for cleanup to complete
  });

  // Function to kill Python backend process
  function killPythonBackend() {
    if (pythonProcess && pythonProcessPid) {
      console.log(`🛑 Killing Python backend process (PID: ${pythonProcessPid})...`);
      
      if (process.platform === 'win32') {
        // Windows: Use taskkill to forcefully kill the process and its children
        exec(`taskkill /pid ${pythonProcessPid} /T /F`, (error, stdout, stderr) => {
          if (error) {
            // Don't show error if process is already dead
            if (!error.message.includes('not found') && !error.message.includes('No such process')) {
              console.error(`❌ Error killing process: ${error.message}`);
            } else {
              console.log(`✅ Process already terminated`);
            }
          } else {
            console.log(`✅ Python backend killed successfully`);
          }
        });
      } else {
        // Unix-like: Use SIGKILL
        try {
          process.kill(pythonProcessPid, 'SIGKILL');
          console.log(`✅ Python backend killed successfully`);
        } catch (error) {
          // Don't show error if process is already dead
          if (!error.message.includes('No such process') && !error.message.includes('ESRCH')) {
            console.error(`❌ Error killing process: ${error.message}`);
          } else {
            console.log(`✅ Process already terminated`);
          }
        }
      }
      
      pythonProcess = null;
      pythonProcessPid = null;
    }
  }

  // Enhanced cleanup function that only kills backend processes
  function forceKillBackendProcesses(callback) {
    console.log(`🛑 Force killing backend Python processes...`);
    
    if (process.platform === 'win32') {
      // Kill processes by command line containing run.py
      exec(`wmic process where "commandline like '%run.py%'" delete`, (error, stdout, stderr) => {
        if (error && !error.message.includes('No Instance(s) Available')) {
          console.error(`❌ Error killing backend processes: ${error.message}`);
        } else {
          console.log(`✅ Backend processes cleaned up`);
        }
        if (callback) callback();
      });
    } else {
      // Unix-like: Kill processes running run.py
      exec(`pkill -f run.py`, (error, stdout, stderr) => {
        if (error) {
          console.log(`✅ No backend processes found to kill`);
        } else {
          console.log(`✅ Backend processes killed successfully`);
        }
        if (callback) callback();
      });
    }
  }

  app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
      // Try specific process first, then fallback to all Python processes
      killPythonBackend();
      setTimeout(() => {
        forceKillBackendProcesses(() => {
          // Wait a bit more to ensure processes are fully terminated
          setTimeout(() => {
            console.log('✅ Cleanup complete, quitting app...');
            app.quit();
          }, 500);
        });
      }, 1000); // Wait 1 second for initial kill to complete
    }
  });
  
  // Track if we've already run cleanup
  let isQuitting = false;
  
  // Also kill backend when app is quitting
  app.on('before-quit', (event) => {
    if (!isQuitting) {
      // Prevent immediate quit on first call, allow cleanup to complete
      event.preventDefault();
      isQuitting = true;
      
      console.log('🛑 App quitting, cleaning up Python backend...');
      
      // Try specific process first
      killPythonBackend();
      
      // Force kill backend processes and wait for completion
      setTimeout(() => {
        forceKillBackendProcesses(() => {
          // Wait a bit more to ensure processes are fully terminated
          setTimeout(() => {
            console.log('✅ Cleanup complete, exiting...');
            app.exit(0);
          }, 500);
        });
      }, 1000);
    }
  });

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});


