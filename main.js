const { app, BrowserWindow } = require("electron");
const { spawn } = require("child_process");
const http = require("http");

let backendProcess;

function waitForBackend(url, retries = 40) {
  return new Promise((resolve) => {
    const check = (left) => {
      http
        .get(url, () => resolve(true))
        .on("error", () => {
          if (left <= 0) return resolve(false);
          setTimeout(() => check(left - 1), 500);
        });
    };
    check(retries);
  });
}

async function createWindow() {
  const win = new BrowserWindow({
    width: 1400,
    height: 900,
    autoHideMenuBar: true,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  await waitForBackend("http://127.0.0.1:5000");
  win.loadURL("http://127.0.0.1:5000");
}

app.whenReady().then(() => {
  const pythonCmd = process.platform === "win32" ? "py" : "python3";

  backendProcess = spawn(pythonCmd, ["app.py"], {
    cwd: __dirname,
    shell: false,
  });

  backendProcess.stdout.on("data", (data) => console.log("[PYTHON]", data.toString()));
  backendProcess.stderr.on("data", (data) => console.error("[PYTHON ERROR]", data.toString()));

  createWindow();
});

app.on("window-all-closed", () => {
  if (backendProcess) backendProcess.kill();
  if (process.platform !== "darwin") app.quit();
});
