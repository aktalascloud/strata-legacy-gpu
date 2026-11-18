import { test } from 'node:test';
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { createServer } from 'node:net';
import { ROOMY_HOST } from './helpers/hardware.mjs';

test('compaction settings validate, persist across host restart, and preserve other state', { timeout: 30000 }, async t => {
  const home = await mkdtemp(join(tmpdir(), 'strata-compact-settings-'));
  const socket = createServer(); await new Promise(r => socket.listen(0, '127.0.0.1', r));
  const port = socket.address().port; await new Promise(r => socket.close(r));
  let host;
  const start = async () => {
    host = spawn(process.execPath, ['server/index.mjs'], { cwd: resolve(import.meta.dirname, '..'),
      env: { ...process.env, STRATA_HOME: home, STRATA_INSTALL_DIR: join(home, 'install'), STRATA_MODELS_DIR: join(home, 'models'), STRATA_PORT: String(port), STRATA_FORCE_DEMO: '1', STRATA_TEST_HARDWARE: ROOMY_HOST }, stdio: 'ignore' });
    for (let i = 0; i < 120; i++) { try { const r = await fetch(`http://127.0.0.1:${port}/api/agent/compaction`); if (r.ok) return; } catch {} await new Promise(r => setTimeout(r, 100)); }
    throw new Error('test host did not start');
  };
  const stop = async () => { if (host?.exitCode === null) { const done = new Promise(r => host.once('exit', r)); host.kill(); await done; } };
  t.after(async () => { await stop(); try { await rm(home, { recursive: true, force: true, maxRetries: 3 }); } catch {} });
  const request = (method, body) => fetch(`http://127.0.0.1:${port}/api/agent/compaction`, { method, ...(body ? { headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) } : {}) });
  await start();
  assert.deepEqual(await (await request('GET')).json(), { thresholdTokens: 0, keepMessages: 0 });
  assert.equal((await fetch(`http://127.0.0.1:${port}/api/setup/step`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ step: 2, dismissed: true }) })).status, 200);
  assert.equal((await request('POST', { thresholdTokens: 50000, keepMessages: 5 })).status, 200);
  assert.equal((await request('POST', { thresholdTokens: -1, keepMessages: 5 })).status, 400);
  await stop(); await start();
  assert.deepEqual(await (await request('GET')).json(), { thresholdTokens: 50000, keepMessages: 5 });
  assert.equal((await (await fetch(`http://127.0.0.1:${port}/api/setup`)).json()).dismissed, true);
});
