const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("agent", {
  send: (message) => ipcRenderer.invoke("agent:send", message),
  reset: () => ipcRenderer.invoke("agent:reset"),
  openOutput: () => ipcRenderer.invoke("agent:open-output"),
});
