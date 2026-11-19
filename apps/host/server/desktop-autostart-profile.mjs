import { createServer } from 'node:net';
import { spawn } from 'node:child_process';
import { lstatSync, readFileSync, createReadStream, statSync, renameSync, unlinkSync, writeFileSync } from 'node:fs';
import { createHash, randomUUID } from 'node:crypto';
import { basename, dirname, isAbsolute, join } from 'node:path';
import { fileURLToPath } from 'node:url';

export function desktopAutostartConfig(env = process.env) {
  const model = env.STRATA_DESKTOP_AUTOSTART_MODEL;
  const port = env.STRATA_DESKTOP_AUTOSTART_PORT;
  if (!model && !port) return null;
  if (!/^[a-z0-9](?:[a-z0-9_-]|\.(?!\.)){0,79}$/.test(model ?? '') || port !== '8093') {
    throw new Error('Desktop autostart requires a valid model and port 8093.');
  }
  return { model, port: 8093 };
}

// Recover a model moved to the root of the configured library, keeping every other setting.
export function relocateAutostartModel(configPath, modelsDir) {
  if (!isAbsolute(modelsDir ?? '') || !lstatSync(configPath, { throwIfNoEntry: false })?.isFile()) return false;
  const config = JSON.parse(readFileSync(configPath, 'utf8').replace(/^\uFEFF/, ''));
  const isFile = path => statSync(path, { throwIfNoEntry: false })?.isFile() === true;
  let changed = false;
  let unresolved = false;
  function relocate(path) {
    if (typeof path !== 'string' || !isAbsolute(path) || !/\.gguf$/i.test(path) || isFile(path)) return path;
    const candidate = join(modelsDir, basename(path));
    const shard = /^(.*)-\d{5}-of-(\d{5})(\.gguf)$/i.exec(candidate);
    const complete = isFile(candidate) && (!shard || (
      Number(shard[2]) > 0 && Number(shard[2]) <= 100 &&
      Array.from({ length: Number(shard[2]) }, (_, i) =>
        isFile(`${shard[1]}-${String(i + 1).padStart(5, '0')}-of-${shard[2]}${shard[3]}`)).every(Boolean)
    ));
    if (!complete) { unresolved = true; return path; }
    changed = true;
    return candidate;
  }
  for (const key of ['args', 'user_args', 'args_written']) {
    const args = config[key];
    if (!Array.isArray(args)) continue;
    for (let i = 0; i + 1 < args.length; i++) {
      if (['--native', '--ple-gguf'].includes(args[i])) args[++i] = relocate(args[i]);
    }
  }
  for (const key of ['model', 'mmproj']) if (config.vision && key in config.vision) config.vision[key] = relocate(config.vision[key]);
  if (!changed || unresolved) return false;
  const temp = `${configPath}.${randomUUID()}.tmp`;
  writeFileSync(temp, JSON.stringify(config, null, 2) + '\n', { flag: 'wx', mode: 0o600 });
  try { renameSync(temp, configPath); }
  catch (error) { unlinkSync(temp); throw error; }
  return true;
}

export function legacyLocalConfig(config, profile, args, dependencyDirs = null) {
  if (!profile || args?.model !== profile.model || args?.port !== profile.port) return config;
  if (config.host !== '127.0.0.1' || (config.api_key != null && config.api_key !== 'none')) {
    throw new Error('The selected legacy profile must use loopback without an API key.');
  }
  if (dependencyDirs) {
    const same = (a, b) => typeof a === 'string' && a.replace(/[\\/]+$/, '').toLowerCase() === b.replace(/[\\/]+$/, '').toLowerCase();
    if (config.exe !== 'component:strata-engine' || !Array.isArray(config.lib_dirs) || config.lib_dirs.length !== 2 || !config.lib_dirs.every((dir, i) => same(dir, dependencyDirs[i]))) {
      throw new Error('The model must use the verified engine component and library directories.');
    }
  }
  return { ...config, port: profile.port, api_key: 'none' };
}

export function autostartPortAvailable(port) {
  return new Promise(resolve => {
    const server = createServer();
    server.once('error', () => resolve(false));
    server.listen(port, '127.0.0.1', () => server.close(() => resolve(true)));
  });
}

export function watchAutostartJob(native, id, onFailure, delay = 500, onState = () => {}) {
  let last = null;
  const check = () => {
    const job = native.state().jobs.find(row => row.id === id);
    const state = job?.state ?? 'missing';
    if (state !== last) { last = state; onState(state); }
    if (!job || job.state === 'error' || job.state === 'cancelled') {
      onFailure(job?.error ?? 'The model start did not complete.');
    } else if (job.state === 'running') {
      setTimeout(check, delay).unref();
    }
  };
  check();
}

export async function shutdownLegacy(native, finish, lock, portAvailable = autostartPortAvailable) {
  await native.close();
  if (!await portAvailable(8093)) throw new Error('Port 8093 is still in use.');
  await finish();
  lock.stdin.end();
}

/** External CUDA and vision libraries are outside the component's own manifest. */
export async function verifyLegacyDependencies(receiptPath, expectedHash) {
  if (!isAbsolute(receiptPath ?? '') || !/^[a-f\d]{64}$/i.test(expectedHash ?? '')) throw new Error('An absolute dependency receipt and its SHA-256 are required.');
  const receiptStat = lstatSync(receiptPath);
  if (!receiptStat.isFile() || receiptStat.size > 65536) throw new Error('Invalid dependency receipt.');
  const raw = readFileSync(receiptPath);
  if (createHash('sha256').update(raw).digest('hex') !== expectedHash.toLowerCase()) throw new Error('Dependency receipt SHA-256 mismatch.');
  const receipt = JSON.parse(raw.toString('utf8'));
  const records = receipt.external_files;
  const components = new Map();
  for (const record of receipt.files ?? []) {
    const name = basename(record?.path ?? '').toLowerCase();
    if (!['strata.exe','strata_kq.dll','strata-vision.exe'].includes(name) || components.has(name) || !/^[a-f\d]{64}$/i.test(record.sha256 ?? '')) throw new Error('Invalid reviewed engine receipt.');
    components.set(name, record.sha256.toLowerCase());
  }
  if (!components.has('strata.exe') || !components.has('strata-vision.exe')) throw new Error('Incomplete reviewed engine receipt.');
  const required = new Set(['cudart64_12.dll','cublas64_12.dll','cublaslt64_12.dll','libomp.dll','msvcp140_atomic_wait.dll','msvcp140.dll','vcomp140.dll','vcruntime140_1.dll','vcruntime140.dll']);
  const cuda = new Set(['cudart64_12.dll','cublas64_12.dll','cublaslt64_12.dll']);
  const directories = [null, null];
  if (!Array.isArray(records) || records.length !== required.size) throw new Error('Dependency receipt has an incomplete DLL list.');
  for (const record of records) {
    const name = basename(record?.path ?? '').toLowerCase();
    if (!required.delete(name) || !isAbsolute(record.path) || !/^[a-f\d]{64}$/i.test(record.sha256 ?? '') || !lstatSync(record.path).isFile()) throw new Error('Dependency receipt has an invalid DLL.');
    const i = cuda.has(name) ? 0 : 1;
    const dir = dirname(record.path);
    if (directories[i] !== null && directories[i].toLowerCase() !== dir.toLowerCase()) throw new Error('Dependency DLLs must use the reviewed directories.');
    directories[i] = dir;
    const hash = createHash('sha256');
    for await (const chunk of createReadStream(record.path)) hash.update(chunk);
    if (hash.digest('hex') !== record.sha256.toLowerCase()) throw new Error(`Dependency SHA-256 mismatch: ${name}`);
  }
  return { directories, components };
}

export function verifyLegacyComponent(root, proof) {
  const manifest = JSON.parse(readFileSync(join(root, 'engine-component.json'), 'utf8'));
  if (manifest.entrypoint !== 'strata.exe' || !Array.isArray(manifest.files) || manifest.files.length !== proof.components.size) throw new Error('The engine component differs from the benchmark-verified build.');
  for (const [name, hash] of proof.components) {
    const entry = manifest.files?.find(item => item.path?.toLowerCase() === name);
    if (!entry || entry.sha256?.toLowerCase() !== hash) throw new Error('The engine component differs from the benchmark-verified build.');
  }
}

/** Take the same lock as the old launcher; keep it until the host closes the pipe. */
export async function acquireLegacyOwner(python, lockPath, port) {
  if (process.platform !== 'win32' || !isAbsolute(lockPath ?? '')) throw new Error('An absolute Windows legacy lock path is required.');
  if (!lstatSync(lockPath).isFile()) throw new Error('The legacy lock must be an existing regular file.');
  const helper = fileURLToPath(new URL('./desktop-legacy-lock.py', import.meta.url));
  const child = spawn(python, [helper, lockPath], { windowsHide: true, stdio: ['pipe', 'pipe', 'ignore'] });
  try {
    await new Promise((resolve, reject) => {
      let output = '';
      const timer = setTimeout(() => reject(new Error('Legacy owner lock timed out.')), 10000);
      child.once('error', reject);
      child.once('exit', () => reject(new Error('The legacy owner lock is held or unavailable.')));
      child.stdout.on('data', chunk => {
        output += chunk;
        if (output.includes('\n')) { clearTimeout(timer); output.trim() === 'locked' ? resolve() : reject(new Error('Legacy owner lock failed.')); }
      });
      child.once('close', () => clearTimeout(timer));
    });
    if (!await autostartPortAvailable(port)) throw new Error(`Port ${port} is already in use.`);
    return child;
  } catch (error) {
    const closed = child.exitCode === null ? new Promise(resolve => child.once('close', resolve)) : Promise.resolve();
    child.stdin.end();
    child.kill();
    await closed;
    throw error;
  }
}
