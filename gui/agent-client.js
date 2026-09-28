const { spawn: spawnProcess } = require('node:child_process');

function createAgentClient({ cwd, spawn = spawnProcess }) {
  let sessionId = null;
  let busy = false;
  return {
    reset() {
      if (busy) return { ok: false, text: '현재 응답이 끝난 뒤 초기화해주세요.' };
      sessionId = null;
      return { ok: true };
    },
    async send(message) {
      if (typeof message !== 'string' || !message.trim()) return { ok: false, text: '메시지를 입력해주세요.' };
      if (busy) return { ok: false, text: '현재 요청이 진행 중입니다.' };
      busy = true;
      try {
        return await new Promise(resolve => {
          const args = ['-p', '--output-format', 'json'];
          if (sessionId) args.push('--resume', sessionId);
          // Windows npm .cmd launchers need a shell. Only fixed flags and a validated
          // session UUID go through it; all user input is sent as UTF-8 stdin.
          const proc = spawn('claude', args, { cwd, shell: process.platform === 'win32', windowsHide: true });
          let stdout = '';
          let stderr = '';
          proc.stdout.setEncoding?.('utf8');
          proc.stderr.setEncoding?.('utf8');
          proc.stdout.on('data', chunk => { stdout += chunk.toString(); });
          proc.stderr.on('data', chunk => { stderr += chunk.toString(); });
          proc.on('error', error => resolve({ ok: false, text: `Claude Code CLI 실행 실패: ${error.message}\n이 폴더의 터미널에서 claude 로그인과 PATH를 확인해주세요.` }));
          proc.stdin.on('error', error => resolve({ ok: false, text: `Claude 입력 전달 실패: ${error.message}` }));
          proc.on('close', code => {
            let data;
            try { data = JSON.parse(stdout); } catch {
              resolve({ ok: false, text: (stderr || stdout || `Claude 종료 코드: ${code}`).trim() });
              return;
            }
            if (code !== 0 || data.is_error) {
              resolve({ ok: false, text: data.result || stderr || `Claude 종료 코드: ${code}` });
              return;
            }
            if (/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i.test(data.session_id || '')) sessionId = data.session_id;
            if (data.permission_denials?.length) {
              const command = sessionId ? `claude --resume ${sessionId}` : 'claude';
              resolve({ ok: false, text: `${data.result || ''}\n\n도구 권한 승인이 필요합니다. 저장소 루트 터미널에서 ${command} 명령으로 이어서 확인해주세요.` });
              return;
            }
            resolve({ ok: true, text: data.result || '(응답이 비어 있습니다)' });
          });
          proc.stdin.end(message);
        });
      } finally { busy = false; }
    },
  };
}

module.exports = { createAgentClient };
