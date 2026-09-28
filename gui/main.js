// 네이버 블로그 에이전트 GUI — Electron 메인 프로세스
//
// 이 앱은 직접 글을 쓰지 않는다. 버튼/채팅으로 받은 메시지를 그대로
// Claude Code CLI(`claude -p`)에 넘기고, 응답을 화면에 표시하는 얇은 래퍼다.
// 실제 워크플로우(키워드 발굴, 본문 작성, 검증, 패키징)는 전부
// 저장소 루트의 CLAUDE.md / .claude/agents / .claude/skills가 정의한 대로
// Claude Code가 수행한다.

const { app, BrowserWindow, ipcMain, shell } = require("electron");
const path = require("path");
const fs = require("fs");
const { createAgentClient } = require("./agent-client");

// gui/ 폴더의 부모 = 저장소 루트. CLAUDE.md와 .claude/가 여기 있어야
// Claude Code가 이 스킬 세트를 인식한다.
const SKILL_ROOT = path.join(__dirname, "..");

let mainWindow;
const agentClient = createAgentClient({ cwd: SKILL_ROOT });
const smoke = process.argv.includes("--smoke");

function createWindow() {
  mainWindow = new BrowserWindow({
    show: !smoke,
    width: 1180,
    height: 820,
    minWidth: 860,
    minHeight: 600,
    backgroundColor: "#FAF9F5",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  if (smoke) {
    const timeout = setTimeout(() => app.exit(1), 15000);
    mainWindow.webContents.once("did-finish-load", async () => {
      try {
        const ready = await mainWindow.webContents.executeJavaScript('Boolean(window.agent && document.getElementById("send"))');
        console.log(ready ? "GUI_SMOKE_OK" : "GUI_SMOKE_FAILED");
        clearTimeout(timeout);
        app.exit(ready ? 0 : 1);
      } catch { app.exit(1); }
    });
    mainWindow.webContents.once("did-fail-load", () => app.exit(1));
  }
  mainWindow.setMenuBarVisibility(false);
  mainWindow.loadFile(path.join(__dirname, "renderer", "index.html"));
}

app.whenReady().then(() => {
  createWindow();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

// 입력은 stdin으로 전달하며 각 GUI 세션의 ID만 이어 쓴다.
ipcMain.handle("agent:send", async (_event, message) => agentClient.send(message));
ipcMain.handle("agent:reset", async () => agentClient.reset());

// post.html 등 생성된 파일이 있는 output 폴더를 탐색기로 연다.
ipcMain.handle("agent:open-output", async () => {
  const outputDir = path.join(SKILL_ROOT, "output");
  await fs.promises.mkdir(outputDir, { recursive: true });
  const error = await shell.openPath(outputDir);
  return { ok: !error, text: error };
});
