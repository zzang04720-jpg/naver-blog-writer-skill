// 네이버 블로그 에이전트 GUI — Electron 메인 프로세스
//
// 이 앱은 직접 글을 쓰지 않는다. 버튼/채팅으로 받은 메시지를 그대로
// Claude Code CLI(`claude -p`)에 넘기고, 응답을 화면에 표시하는 얇은 래퍼다.
// 실제 워크플로우(키워드 발굴, 본문 작성, 검증, 패키징)는 전부
// 저장소 루트의 CLAUDE.md / .claude/agents / .claude/skills가 정의한 대로
// Claude Code가 수행한다.

const { app, BrowserWindow, ipcMain, shell } = require("electron");
const path = require("path");
const { spawn } = require("child_process");

// gui/ 폴더의 부모 = 저장소 루트. CLAUDE.md와 .claude/가 여기 있어야
// Claude Code가 이 스킬 세트를 인식한다.
const SKILL_ROOT = path.join(__dirname, "..");

let mainWindow;
let sessionStarted = false;

function createWindow() {
  mainWindow = new BrowserWindow({
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

// 렌더러에서 메시지 하나를 받아 `claude -p`로 넘기고 텍스트 응답을 돌려준다.
// 두 번째 메시지부터는 --continue로 같은 대화(세션)를 이어간다.
ipcMain.handle("agent:send", async (_event, message) => {
  return new Promise((resolve) => {
    if (!message || !message.trim()) {
      resolve({ ok: false, text: "빈 메시지는 보낼 수 없습니다." });
      return;
    }

    const args = ["-p", message, "--output-format", "text"];
    if (sessionStarted) args.push("--continue");

    const proc = spawn("claude", args, {
      cwd: SKILL_ROOT,
      shell: true,
      windowsHide: true,
    });

    let stdout = "";
    let stderr = "";

    proc.stdout.on("data", (chunk) => {
      stdout += chunk.toString();
    });
    proc.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });

    proc.on("error", (err) => {
      resolve({
        ok: false,
        text:
          "claude 명령을 실행할 수 없습니다. Claude Code CLI가 설치되어 있고 " +
          "PATH에 등록되어 있는지 확인해주세요.\n\n오류: " + err.message,
      });
    });

    proc.on("close", (code) => {
      sessionStarted = true;
      if (code !== 0 && !stdout.trim()) {
        resolve({
          ok: false,
          text: (stderr || `claude 프로세스가 오류 코드 ${code}로 종료됐습니다.`).trim(),
        });
        return;
      }
      resolve({ ok: true, text: stdout.trim() || "(응답이 비어 있습니다)" });
    });
  });
});

// 새 대화로 다시 시작하고 싶을 때 (예: "처음부터 다시" 버튼)
ipcMain.handle("agent:reset", async () => {
  sessionStarted = false;
  return { ok: true };
});

// post.html 등 생성된 파일이 있는 output 폴더를 탐색기로 연다.
ipcMain.handle("agent:open-output", async () => {
  const outputDir = path.join(SKILL_ROOT, "output");
  await shell.openPath(outputDir);
  return { ok: true };
});
