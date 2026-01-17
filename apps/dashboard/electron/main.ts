import { app, BrowserWindow, ipcMain, dialog } from "electron";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { spawn } from "node:child_process";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// The built directory structure
//
// ├─┬─┬ dist
// │ │ └── index.html
// │ │
// │ ├─┬ dist-electron
// │ │ ├── main.js
// │ │ └── preload.mjs
// │
process.env.APP_ROOT = path.join(__dirname, "..");

// 🚧 Use ['ENV_NAME'] avoid vite:define plugin - Vite@2.x
export const VITE_DEV_SERVER_URL = process.env["VITE_DEV_SERVER_URL"];
export const MAIN_DIST = path.join(process.env.APP_ROOT, "dist-electron");
export const RENDERER_DIST = path.join(process.env.APP_ROOT, "dist");

process.env.VITE_PUBLIC = VITE_DEV_SERVER_URL
	? path.join(process.env.APP_ROOT, "public")
	: RENDERER_DIST;

let win: BrowserWindow | null;

function createWindow() {
	win = new BrowserWindow({
		icon: path.join(process.env.VITE_PUBLIC, "electron-vite.svg"),
		webPreferences: {
			preload: path.join(__dirname, "preload.mjs"),
		},
	});

	// Test active push message to Renderer-process.
	win.webContents.on("did-finish-load", () => {
		win?.webContents.send("main-process-message", new Date().toLocaleString());
	});

	// Open DevTools in production to see errors
	if (!VITE_DEV_SERVER_URL) {
		win.webContents.openDevTools();
	}

	// Log console messages from renderer
	win.webContents.on("console-message", (event, level, message, line, sourceId) => {
		console.log(`[Renderer Console] ${message}`);
	});

	if (VITE_DEV_SERVER_URL) {
		win.loadURL(VITE_DEV_SERVER_URL);
	} else {
		// win.loadFile('dist/index.html')
		win.loadFile(path.join(RENDERER_DIST, "index.html"));
	}
}

// Quit when all windows are closed, except on macOS. There, it's common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
app.on("window-all-closed", () => {
	if (process.platform !== "darwin") {
		app.quit();
		win = null;
	}
});

app.on("activate", () => {
	// On OS X it's common to re-create a window in the app when the
	// dock icon is clicked and there are no other windows open.
	if (BrowserWindow.getAllWindows().length === 0) {
		createWindow();
	}
});

// IPC Handlers
ipcMain.handle("select-file", async () => {
	try {
		const result = await dialog.showOpenDialog({
			properties: ["openFile"],
			filters: [
				{
					name: "Executables",
					extensions: [
						"exe",
						"bat",
						"cmd",
						"sh",
						"app",
						"jar",
						"py",
						"pl",
						"rb",
						"com",
						"scr",
						"pif",
						"cpl",
						"msc",
					],
				},
				{ name: "All Files", extensions: ["*"] },
			],
		});

		if (!result.canceled && result.filePaths.length > 0) {
			return result.filePaths[0];
		}
		return null;
	} catch (error) {
		console.error("Error selecting file:", error);
		return null;
	}
});

ipcMain.handle("save-config", async (_event, config) => {
	try {
		const fs = await import("node:fs/promises");
		const configPath = path.join(app.getPath("userData"), "config.json");
		await fs.writeFile(configPath, JSON.stringify(config, null, 2), "utf-8");
		console.log("Config saved to:", configPath);
		return { success: true, path: configPath };
	} catch (error) {
		console.error("Error saving config:", error);
		return { success: false, error: String(error) };
	}
});

ipcMain.handle("load-config", async () => {
	try {
		const fs = await import("node:fs/promises");
		const configPath = path.join(app.getPath("userData"), "config.json");
		const data = await fs.readFile(configPath, "utf-8");
		const config = JSON.parse(data);
		console.log("Config loaded from:", configPath);
		return { success: true, data: config };
	} catch (error) {
		console.error("Error loading config:", error);
		return { success: false, error: String(error) };
	}
});

ipcMain.handle("execute-urmom", async (_event, args: string[] = []) => {
	try {
		// Determine the path to urmom.exe
		// In production, it's in the resources directory
		// In development, we'll look for it in the sibling urmom/dist folder
		let urmomPath: string;
		
		if (app.isPackaged) {
			// Production: extraResources are placed in the resources directory
			urmomPath = path.join(process.resourcesPath, "urmom.exe");
		} else {
			// Development: look in the urmom/dist folder
			urmomPath = path.join(__dirname, "..", "..", "urmom", "dist", "urmom.exe");
		}

		console.log("Attempting to execute urmom.exe from:", urmomPath);

		// Check if file exists
		const fs = await import("node:fs/promises");
		try {
			await fs.access(urmomPath);
		} catch {
			return { 
				success: false, 
				error: `urmom.exe not found at ${urmomPath}. Make sure the Python app is built.` 
			};
		}

		// Execute the binary
		const child = spawn(urmomPath, args, {
			detached: false,
			stdio: ["ignore", "pipe", "pipe"],
		});

		let stdout = "";
		let stderr = "";

		child.stdout?.on("data", (data) => {
			stdout += data.toString();
		});

		child.stderr?.on("data", (data) => {
			stderr += data.toString();
		});

		// Return immediately with the process info
		// You can also wait for the process to complete if needed
		return new Promise((resolve) => {
			child.on("close", (code) => {
				console.info(`urmom.exe exited with code ${code}`);
				resolve({
					success: code === 0,
					code,
					stdout,
					stderr,
					path: urmomPath,
				});
			});

			child.on("error", (error) => {
				console.error("Error executing urmom.exe:", error);
				resolve({
					success: false,
					error: String(error),
					path: urmomPath,
				});
			});
		});
	} catch (error) {
		console.error("Error in execute-urmom handler:", error);
		return { success: false, error: String(error) };
	}
});

app.whenReady().then(createWindow);
