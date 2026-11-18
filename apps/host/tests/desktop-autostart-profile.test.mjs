import test from 'node:test';
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { createServer } from 'node:net';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { acquireLegacyOwner, autostartPortAvailable, desktopAutostartConfig, legacyLocalConfig, relocateAutostartModel, shutdownLegacy, verifyLegacyComponent, verifyLegacyDependencies, watchAutostartJob } from '../server/desktop-autostart-profile.mjs';
import { createHash } from 'node:crypto';

const enabled = { STRATA_DESKTOP_AUTOSTART_MODEL: 'swift-1.5-iq3-s', STRATA_DESKTOP_AUTOSTART_PORT: '8093' };
const profile = { model: 'swift-1.5-iq3-s', port: 8093 };

test('shutdown keeps the owner lock until the engine stops and the port is free', async () => {
  let stop, released = false, cleaned = false;
  const native = { close: () => new Promise(resolve => { stop = resolve; }) };
  const lock = { stdin: { end: () => { released = true; } } };
  const pending = shutdownLegacy(native, async () => { cleaned = true; }, lock, async () => true);
  assert.equal(released, false); assert.equal(cleaned, false); stop(); await pending;
  assert.equal(cleaned, true); assert.equal(released, true);
  released = false;
  await assert.rejects(shutdownLegacy({ close: async () => { throw new Error('stop failed'); } }, async () => {}, lock, async () => true));
  assert.equal(released, false);
  await assert.rejects(shutdownLegacy({ close: async () => {} }, async () => {}, lock, async () => false), /still in use/);
  assert.equal(released, false);
});

test('ordinary saved settings survive a new start while verified library paths stay fixed', () => {
  const dirs = ['C:\\verified\\cuda', 'C:\\verified\\vision'];
  const before = { host: '127.0.0.1', exe: 'component:strata-engine', lib_dirs: dirs, sampling: { top_k: 20 } };
  const saved = { ...before, sampling: { top_k: 25 } };
  assert.equal(legacyLocalConfig(saved, profile, profile, dirs).sampling.top_k, 25);
  assert.throws(() => legacyLocalConfig({ ...saved, lib_dirs: ['C:\\other', dirs[1]] }, profile, profile, dirs), /verified engine/);
  assert.throws(() => legacyLocalConfig({ ...saved, exe: 'C:\\other.exe' }, profile, profile, dirs), /verified engine/);
});

test('failed and cancelled asynchronous model starts are reported; a successful start is not a failure', async () => {
  for (const state of ['error', 'cancelled']) {
    const failure = await new Promise(resolve => watchAutostartJob({ state: () => ({ jobs: [{ id: '1', state, error: 'start failed' }] }) }, '1', resolve));
    assert.equal(failure, 'start failed');
  }
  let failed = false;
  watchAutostartJob({ state: () => ({ jobs: [{ id: '1', state: 'done' }] }) }, '1', () => { failed = true; });
  assert.equal(failed, false);
});

test('autostart can repair a flattened GGUF library only when all model and projector files exist', async t => {
  const dir = await mkdtemp(join(tmpdir(), 'strata-relocated-model-'));
  t.after(() => rm(dir, {recursive: true, force: true}));
  const part = n => `swift-0000${n}-of-00002.gguf`;
  const old = join(dir, 'previous', part(1));
  const projector = join(dir, 'previous', 'projector.gguf');
  const configPath = join(dir, 'config.json');
  const config = { args: ['--native', old, '--kv', 'q4_0'], user_args: ['--ple-gguf', old],
    args_written: ['--native', old], vision: { model: old, mmproj: projector, threads: 16 } };
  const serialized = JSON.stringify(config);
  await writeFile(configPath, serialized);
  await writeFile(join(dir, part(1)), 'GGUF');
  await writeFile(join(dir, 'projector.gguf'), 'GGUF');
  assert.equal(relocateAutostartModel(configPath, dir), false);
  assert.equal(await readFile(configPath, 'utf8'), serialized);
  await writeFile(join(dir, part(2)), 'GGUF');
  assert.equal(relocateAutostartModel(configPath, dir), true);
  const saved = JSON.parse(await readFile(configPath, 'utf8'));
  const current = join(dir, part(1));
  assert.deepEqual(saved, { args: ['--native', current, '--kv', 'q4_0'], user_args: ['--ple-gguf', current],
    args_written: ['--native', current], vision: { model: current, mmproj: join(dir, 'projector.gguf'), threads: 16 } });
  assert.equal(relocateAutostartModel(configPath, dir), false);
});

test('the autostart watcher reports state changes before its failure callback', async () => {
  const events = []; let state = 'running';
  const failed = new Promise(resolve => {
    watchAutostartJob({ state: () => ({ jobs: [{ id: 'job-1', state }] }) }, 'job-1', reason => { events.push('failure'); resolve(reason); }, 5, next => events.push(next));
  });
  await new Promise(resolve => setTimeout(resolve, 10));
  state = 'cancelled';
  assert.equal(await failed, 'The model start did not complete.');
  assert.deepEqual(events, ['running', 'cancelled', 'failure']);
});

test('a live owner file blocks startup and releases the acquired lock', { skip: process.platform !== 'win32' || !process.env.TEST_PYTHON }, async t => {
  const dir = await mkdtemp(join(tmpdir(), 'strata-owner-check-'));
  t.after(() => rm(dir, { recursive: true, force: true }));
  const lock = join(dir, 'server.lock');
  await writeFile(lock, '0');
  await writeFile(join(dir, 'ready.json'), JSON.stringify({ pid: process.pid, created_at: Date.now() / 1000, instance_id: 'test', bound_host: '127.0.0.1', bound_port: 8093 }));
  await assert.rejects(acquireLegacyOwner(process.env.TEST_PYTHON, lock, 8093), /legacy owner lock/);
});

test('dependency receipt is pinned and detects a changed or missing external DLL', async t => {
  const dir = await mkdtemp(join(tmpdir(), 'strata-dll-receipt-'));
  t.after(() => rm(dir, { recursive: true, force: true }));
  const names = ['cudart64_12.dll','cublas64_12.dll','cublasLt64_12.dll','libomp.dll','MSVCP140_ATOMIC_WAIT.dll','MSVCP140.dll','VCOMP140.DLL','VCRUNTIME140_1.dll','VCRUNTIME140.dll'];
  const hash = data => createHash('sha256').update(data).digest('hex');
  const files = [];
  for (const name of names) { const path = join(dir, name); await writeFile(path, name); files.push({ path, sha256: hash(name) }); }
  const raw = JSON.stringify({ external_files: files, files: ['strata.exe','strata_kq.dll','strata-vision.exe'].map(name => ({ path: join(dir, name), sha256: 'a'.repeat(64) })) });
  const receipt = join(dir, 'receipt.json'); await writeFile(receipt, raw);
  const proof = await verifyLegacyDependencies(receipt, hash(raw));
  const manifest = join(dir, 'engine-component.json');
  await writeFile(manifest, JSON.stringify({ entrypoint: 'strata.exe', files: [...proof.components].map(([path, sha256]) => ({ path, sha256 })) }));
  assert.doesNotThrow(() => verifyLegacyComponent(dir, proof));
  await writeFile(manifest, JSON.stringify({ files: [{ path: 'strata.exe', sha256: 'b'.repeat(64) }] }));
  assert.throws(() => verifyLegacyComponent(dir, proof), /benchmark-verified/);
  await assert.rejects(verifyLegacyDependencies(receipt, '0'.repeat(64)), /receipt SHA-256 mismatch/);
  await writeFile(files[0].path, 'changed');
  await assert.rejects(verifyLegacyDependencies(receipt, hash(raw)), /Dependency SHA-256 mismatch/);
  await rm(files[0].path);
  await assert.rejects(verifyLegacyDependencies(receipt, hash(raw)));
});

test('desktop autostart is opt-in and requires an exact model and port', () => {
  assert.equal(desktopAutostartConfig({}), null);
  assert.deepEqual(desktopAutostartConfig(enabled), profile);
  for (const env of [
    { STRATA_DESKTOP_AUTOSTART_MODEL: enabled.STRATA_DESKTOP_AUTOSTART_MODEL },
    { STRATA_DESKTOP_AUTOSTART_PORT: '8093' },
    { ...enabled, STRATA_DESKTOP_AUTOSTART_PORT: '8094' },
    { ...enabled, STRATA_DESKTOP_AUTOSTART_PORT: '8093x' },
    { ...enabled, STRATA_DESKTOP_AUTOSTART_MODEL: '../other' },
    { ...enabled, STRATA_DESKTOP_AUTOSTART_MODEL: 'model\nother' },
  ]) assert.throws(() => desktopAutostartConfig(env));
});

test('only the explicitly selected loopback profile keeps the no-key API', () => {
  const config = { host: '127.0.0.1', port: 8093, args: ['--vram-reserve-mib', '210'], mtp: true };
  const original = structuredClone(config);
  const actual = legacyLocalConfig(config, profile, { model: profile.model, port: profile.port });
  assert.deepEqual(actual, { ...config, api_key: 'none' });
  assert.deepEqual(config, original, 'the source config is not changed');
  assert.notEqual(actual, config, 'the selected launch receives its own config');
  assert.deepEqual(legacyLocalConfig({ ...config, api_key: 'none' }, profile, profile), { ...config, api_key: 'none' });
});

test('other launches keep their existing config and security settings', () => {
  const config = { host: '127.0.0.1', port: 18500, api_key: 'existing-secret', args: ['--prefill', '1536'] };
  const original = structuredClone(config);
  for (const [selected, args] of [
    [null, profile],
    [profile, { ...profile, model: 'another-model' }],
    [profile, { ...profile, port: 18500 }],
  ]) {
    assert.deepEqual(legacyLocalConfig(config, selected, args), original);
    assert.deepEqual(config, original);
  }
});

test('the opted-in launch refuses a non-loopback host or a configured key', () => {
  for (const config of [
    { host: '0.0.0.0' },
    { host: '192.0.2.1' },
    { host: '127.0.0.1', api_key: 'existing-secret' },
  ]) assert.throws(() => legacyLocalConfig(config, profile, profile));
});

test('an occupied loopback port is rejected without contacting the listener', async t => {
  const listener = createServer(socket => socket.destroy());
  await new Promise((resolve, reject) => {
    listener.once('error', reject);
    listener.listen(0, '127.0.0.1', resolve);
  });
  t.after(() => new Promise(resolve => listener.close(resolve)));
  const port = listener.address().port;
  let connections = 0;
  listener.on('connection', () => { connections++; });
  assert.equal(await autostartPortAvailable(port), false);
  assert.equal(connections, 0);
});

test('a released loopback port can be reserved for startup', async () => {
  const listener = createServer();
  await new Promise((resolve, reject) => {
    listener.once('error', reject);
    listener.listen(0, '127.0.0.1', resolve);
  });
  const port = listener.address().port;
  await new Promise(resolve => listener.close(resolve));
  assert.equal(await autostartPortAvailable(port), true);
});

test('the Windows launcher lock excludes another owner until its holder ends', {
  skip: process.platform !== 'win32' || !process.env.TEST_PYTHON
    ? 'requires Windows and TEST_PYTHON' : false,
  timeout: 30000,
}, async t => {
  const directory = await mkdtemp(join(tmpdir(), 'strata-desktop-lock-test-'));
  const lock = join(directory, 'launcher.lock');
  const helper = fileURLToPath(new URL('../server/desktop-legacy-lock.py', import.meta.url));
  const children = new Set();
  t.after(async () => {
    for (const child of children) child.kill();
    await Promise.all([...children].map(child => child.closed));
    await rm(directory, { recursive: true, force: true });
  });
  await writeFile(lock, '0');

  function launch() {
    const child = spawn(process.env.TEST_PYTHON, [helper, lock], { stdio: ['pipe', 'pipe', 'pipe'], windowsHide: true });
    children.add(child);
    child.closed = new Promise((resolve, reject) => {
      child.once('error', reject);
      child.once('close', (code, signal) => { children.delete(child); resolve({ code, signal }); });
    });
    return child;
  }
  function locked(child) {
    return new Promise((resolve, reject) => {
      let output = '';
      child.stdout.on('data', chunk => {
        output += chunk.toString();
        if (output.includes('\n')) {
          try { assert.equal(output.trim(), 'locked'); resolve(); } catch (error) { reject(error); }
        }
      });
      child.once('error', reject);
      child.once('close', code => reject(new Error(`lock helper exited before locking: ${code}`)));
    });
  }

  const first = launch();
  await locked(first);
  const second = launch();
  second.stdin.end();
  assert.equal((await second.closed).code, 1, 'a second owner cannot lock the same byte');
  first.stdin.end();
  assert.equal((await first.closed).code, 0);
  const third = launch();
  await locked(third);
  third.stdin.end();
  assert.equal((await third.closed).code, 0, 'a new owner can lock after release');
  const ready = join(directory, 'ready.json');
  await writeFile(ready, JSON.stringify({ pid: process.pid, created_at: 1, instance_id: 'stale', bound_host: '127.0.0.1', bound_port: 8093 }));
  const reused = launch(); await locked(reused); reused.stdin.end();
  assert.equal((await reused.closed).code, 0, 'a reused PID newer than the ready file is not the old owner');
  await writeFile(ready, JSON.stringify({ pid: process.pid, created_at: Date.now() / 1000, instance_id: 'live', bound_host: '127.0.0.1', bound_port: 8093 }));
  const alive = launch(); alive.stdin.end();
  assert.equal((await alive.closed).code, 1, 'a matching live owner blocks startup');
});
