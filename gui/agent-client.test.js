const test = require('node:test');
const assert = require('node:assert/strict');
const { EventEmitter } = require('node:events');
const { createAgentClient } = require('./agent-client');

function fixture(responses) {
  const calls = [];
  const client = createAgentClient({ cwd: '.', spawn(command, args, options) {
    const proc = new EventEmitter();
    proc.stdout = new EventEmitter();
    proc.stderr = new EventEmitter();
    proc.stdin = new EventEmitter();
    proc.stdin.end = text => {
      calls.push({ command, args, options, text });
      setImmediate(() => {
        const response = responses.shift();
        proc.stdout.emit('data', JSON.stringify(response.body));
        proc.emit('close', response.code || 0);
      });
    };
    return proc;
  }});
  return { client, calls };
}

test('prompt stays on stdin and resume targets its own session', async () => {
  const id = '00000000-0000-4000-8000-000000000001';
  const { client, calls } = fixture([{ body: { session_id: id, result: 'one' } }, { body: { session_id: id, result: 'two' } }]);
  const prompt = 'fictional & echo nope | $(whoami) "한글"';
  assert.equal((await client.send(prompt)).ok, true);
  await client.send('approve');
  assert.equal(calls[0].text, prompt);
  assert.equal(calls[0].args.includes(prompt), false);
  assert.equal(calls[1].args.includes('--continue'), false);
  assert.deepEqual(calls[1].args.slice(-2), ['--resume', id]);
});

test('nonzero exit with partial output is a failure and does not resume', async () => {
  const { client, calls } = fixture([{ code: 1, body: { result: 'partial' } }, { body: { result: 'fresh' } }]);
  assert.equal((await client.send('a')).ok, false);
  await client.send('b');
  assert.equal(calls[1].args.includes('--resume'), false);
});

test('permission denial is visible and busy requests cannot interleave', async () => {
  const { client } = fixture([{ body: { session_id: '00000000-0000-4000-8000-000000000001', result: 'blocked', permission_denials: [{ tool_name: 'Bash' }] } }]);
  const pending = client.send('one');
  assert.equal((await client.send('two')).ok, false);
  assert.equal(client.reset().ok, false);
  const result = await pending;
  assert.equal(result.ok, false);
  assert.match(result.text, /권한/);
  assert.equal(client.reset().ok, true);
});
