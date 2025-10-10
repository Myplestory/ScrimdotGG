const { app, BrowserWindow } = require('electron');
const { spawn, exec } = require('child_process');
const path = require('path');
const process = require('process');

let pythonProcess;
let pythonProcessPid;

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
    const backendPath = path.join(__dirname, '..', 'backend', 'bootstrap.py');
    const backendDir = path.join(__dirname, '..', 'backend');
    
    console.log('🚀 Starting Python backend...');
    console.log('📁 Backend directory:', backendDir);
    console.log('🐍 Backend script:', backendPath);
    
    try {
        // Determine Python command based on environment
        const isDev = process.env.NODE_ENV === 'development';
        const pipenvVenvPath = 'C:\\Users\\Charl\\.virtualenvs\\backend--754moSM\\Scripts\\python.exe';
        
        let pythonCommand, pythonArgs;
        
        if (isDev) {
            // Development: use pipenv virtual environment
            try {
                require('fs').accessSync(pipenvVenvPath);
                pythonCommand = pipenvVenvPath;
                pythonArgs = ['bootstrap.py'];
                console.log(`✅ [DEV] Using pipenv virtual environment Python: ${pythonCommand}`);
            } catch (e) {
                console.log(`❌ [DEV] Pipenv virtual environment not found, falling back to pipenv command`);
                pythonCommand = 'pipenv';
                pythonArgs = ['run', 'python', 'bootstrap.py'];
            }
        } else {
            // Production: use system Python or compiled executable
            const compiledExe = path.join(backendDir, 'bootstrap.exe');
            try {
                require('fs').accessSync(compiledExe);
                pythonCommand = compiledExe;
                pythonArgs = [];
                console.log(`✅ [PROD] Using compiled executable: ${pythonCommand}`);
            } catch (e) {
                pythonCommand = 'python';
                pythonArgs = ['bootstrap.py'];
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
            console.error(`❌ Error killing process: ${error.message}`);
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
          console.error(`❌ Error killing process: ${error.message}`);
        }
      }
      
      pythonProcess = null;
      pythonProcessPid = null;
    }
  }

  // Enhanced cleanup function that only kills backend processes
  function forceKillBackendProcesses() {
    console.log(`🛑 Force killing backend Python processes...`);
    
    if (process.platform === 'win32') {
      // Kill only processes running bootstrap.py (more selective)
      exec(`taskkill /f /fi "WINDOWTITLE eq bootstrap*" /im python.exe`, (error, stdout, stderr) => {
        if (error) {
          // Also try killing by command line containing bootstrap.py
          exec(`wmic process where "commandline like '%bootstrap.py%'" delete`, (error2, stdout2, stderr2) => {
            if (error2 && !error2.message.includes('No Instance(s) Available')) {
              console.error(`❌ Error killing backend processes: ${error2.message}`);
            } else {
              console.log(`✅ Backend processes cleaned up`);
            }
          });
        } else {
          console.log(`✅ Backend processes killed successfully`);
        }
      });
    } else {
      // Unix-like: Kill processes running bootstrap.py
      exec(`pkill -f bootstrap.py`, (error, stdout, stderr) => {
        if (error) {
          console.log(`✅ No backend processes found to kill`);
        } else {
          console.log(`✅ Backend processes killed successfully`);
        }
      });
    }
  }

  app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
      // Try specific process first, then fallback to all Python processes
      killPythonBackend();
      setTimeout(() => {
        forceKillBackendProcesses();
        app.quit();
      }, 1000); // Wait 1 second for initial kill to complete
    }
  });
  
  // Also kill backend when app is quitting
  app.on('before-quit', (event) => {
    // Prevent immediate quit, allow cleanup to complete
    event.preventDefault();
    
    // Try specific process first
    killPythonBackend();
    
    // Force kill backend processes after a short delay
    setTimeout(() => {
      forceKillBackendProcesses();
      // Now allow the app to quit
      setTimeout(() => {
        app.exit(0);
      }, 500);
    }, 1000);
  });

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});


