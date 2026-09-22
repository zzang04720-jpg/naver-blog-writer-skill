const log = document.getElementById("log");
const input = document.getElementById("input");
const sendBtn = document.getElementById("send");
const statusPill = document.getElementById("status-pill");
const resetBtn = document.getElementById("reset-btn");
const openOutputBtn = document.getElementById("open-output");

function appendMessage(role, text) {
  const el = document.createElement("div");
  el.className = `msg ${role}`;
  el.textContent = text;
  log.appendChild(el);
  log.scrollTop = log.scrollHeight;
  return el;
}

function setBusy(busy) {
  sendBtn.disabled = busy;
  document.querySelectorAll(".quick").forEach((b) => (b.disabled = busy));
  statusPill.textContent = busy ? "진행 중..." : "대기 중";
}

async function sendMessage(text) {
  const trimmed = text.trim();
  if (!trimmed) return;

  appendMessage("user", trimmed);
  input.value = "";
  setBusy(true);

  const thinking = appendMessage("agent thinking", "생각 중... (실제 워크플로우 단계라 시간이 걸릴 수 있어요)");

  try {
    const res = await window.agent.send(trimmed);
    thinking.remove();
    appendMessage(res.ok ? "agent" : "error", res.text);
  } catch (e) {
    thinking.remove();
    appendMessage("error", `예상치 못한 오류: ${e.message}`);
  } finally {
    setBusy(false);
    input.focus();
  }
}

sendBtn.addEventListener("click", () => sendMessage(input.value));

input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage(input.value);
  }
});

document.querySelectorAll(".quick").forEach((btn) => {
  btn.addEventListener("click", () => sendMessage(btn.dataset.msg));
});

resetBtn.addEventListener("click", async () => {
  await window.agent.reset();
  log.innerHTML = "";
  appendMessage("agent", "새 대화로 초기화했습니다. \"오늘 글 시작하기\"부터 다시 눌러주세요.");
});

openOutputBtn.addEventListener("click", () => {
  window.agent.openOutput();
});
