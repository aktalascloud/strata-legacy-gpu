import test from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import { mkdirSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createAgentBridge } from '../server/agent/agent-bridge.mjs';
import { createLlmProxy } from '../server/agent/llm-shape.mjs';
import { FREELLM_MODELS, FREELLM_URL } from '../server/freellm.mjs';
import { resolveHarness } from '../server/agent/harness-runtime.mjs';
import { startScriptedWorker } from './helpers/scripted-worker.mjs';

test('delayed request bodies cannot outlive or cross the selected turn', async t => {
  let upstreamCalls = 0, permit = 'turn-1', received;
  const upstream = http.createServer((req, res) => { upstreamCalls++; req.resume(); req.on('end', () => { res.writeHead(200); res.end('ok'); }); });
  await new Promise(resolve => upstream.listen(0, '127.0.0.1', resolve));
  const base = `http://127.0.0.1:${upstream.address().port}/v1`;
  const target = () => permit ? { base, ownerRoute: 'api-free', anonymousFree: true, allowedModels: [FREELLM_MODELS[0]], allowedPermits: [{ id: permit, model: FREELLM_MODELS[0] }] } : null;
  const forward = createLlmProxy({ targetOf: target, samplingNow: () => null });
  const proxy = http.createServer((req, res) => { received?.(); forward(req, res, 'route', '/v1/chat/completions'); });
  await new Promise(resolve => proxy.listen(0, '127.0.0.1', resolve));
  t.after(async () => { await new Promise(resolve => proxy.close(resolve)); await new Promise(resolve => upstream.close(resolve)); });
  async function delayed(nextPermit) {
    let observed;
    const accepted = new Promise(resolve => { received = resolve; });
    const response = new Promise((resolve, reject) => {
      const request = http.request({ host: '127.0.0.1', port: proxy.address().port, method: 'POST', path: '/', headers: { 'content-type': 'application/json' } }, reply => { reply.resume(); reply.on('end', () => resolve(reply.statusCode)); });
      request.on('error', reject);
      request.write('{"model":');
      observed = request;
    });
    await accepted;
    permit = nextPermit;
    observed.end(JSON.stringify(FREELLM_MODELS[0]) + ',"messages":[]}');
    return response;
  }
  assert.equal(await delayed(null), 403, 'cancelled turn');
  permit = 'turn-1';
  assert.equal(await delayed('turn-2'), 403, 'another turn cannot inherit an old request');
  permit = 'turn-3';
  assert.equal(await delayed('turn-3'), 200, 'the original selected turn is still active');
  assert.equal(upstreamCalls, 1);
});

test('the FreeLLM proxy is closed unless a user-selected turn is active', { skip: !resolveHarness({ env: process.env }).ok }, async t => {
  const directory = mkdtempSync(join(tmpdir(), 'strata-free-consent-'));
  const workspace = join(directory, 'workspace'); mkdirSync(workspace);
  const local = await startScriptedWorker();
  const cloud = await startScriptedWorker({ model: FREELLM_MODELS[0], chunkDelayMs: 40 });
  let bridge, acceptedHeld;
  const proxy = createLlmProxy({ targetOf: key => { const target = bridge.llmTarget(key); return target?.anonymousFree ? { ...target, base: cloud.url } : target; }, samplingNow: () => null });
  const front = http.createServer((req, res) => { const match = /^\/api\/internal\/agent-llm\/([^/]+)(\/.*)$/.exec(req.url); if (!match) { res.writeHead(404); return res.end(); } if (acceptedHeld) { const notify = acceptedHeld; acceptedHeld = null; notify(); } proxy(req, res, match[1], match[2]); });
  await new Promise(resolve => front.listen(0, '127.0.0.1', resolve));
  const base = `http://127.0.0.1:${front.address().port}/api/internal/agent-llm`;
  const connection = { id: 'free', provider: 'freellm', name: 'FreeLLM', baseUrl: FREELLM_URL, protocol: 'openai-chat', apiKey: '', models: FREELLM_MODELS.map(id => ({ id, contextMax: 32768, maxOutput: 4096, vision: false, reasoning: true })) };
  bridge = createAgentBridge({ dataDir: directory, localInstances: () => [{ id: 'swift', label: 'Swift', baseUrl: local.url, modelId: 'scripted-model', context: 32768 }], connections: () => [connection], env: process.env, startTimeoutMs: 90_000, proxyBase: base });
  t.after(async () => { await bridge.close(); await local.close(); await cloud.close(); await new Promise(resolve => front.close(resolve)); try { rmSync(directory, { recursive: true, force: true, maxRetries: 3 }); } catch { /* Harness may retain temporary ACLs */ } });
  const send = (key, model) => fetch(`${base}/${key}/v1/chat/completions`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ model, messages: [{ role: 'user', content: 'test' }] }) });
  const localTurn = bridge.runTurn({ chatId: 'local', choice: { instanceId: 'swift' }, message: 'SCRIPT:slow 120', workspacePath: workspace, mode: 'bypass', onFrame() {} });
  for (let i = 0; i < 150 && !local.requests.length; i++) await new Promise(resolve => setTimeout(resolve, 100));
  assert.ok(local.requests.length, 'local turn is active');
  const key = Object.keys(bridge._debug().rt.profile.shapeTargets).find(value => value.startsWith('api-free~free-'));
  assert.ok(key && key.length > 'api-free~free-'.length + 20, 'cloud route has an unguessable capability');
  assert.equal((await send('api-free~free', FREELLM_MODELS[0])).status, 404);
  assert.equal((await send(key, FREELLM_MODELS[0])).status, 404, 'even the capability is closed during local use');
  assert.equal(cloud.requests.length, 0);
  await localTurn;
  assert.equal((await send(key, FREELLM_MODELS[0])).status, 404, 'closed while idle');
  const cloudTurn = bridge.runTurn({ chatId: 'cloud', choice: { connectionId: 'free', modelId: FREELLM_MODELS[0] }, message: 'SCRIPT:slow 120', workspacePath: workspace, mode: 'bypass', onFrame() {} });
  for (let i = 0; i < 150 && !cloud.requests.length; i++) await new Promise(resolve => setTimeout(resolve, 100));
  assert.ok(cloud.requests.length, 'explicitly selected FreeLLM is served');
  const before = cloud.requests.length;
  assert.equal((await send(key, FREELLM_MODELS[1])).status, 400, 'a different unselected free model is forbidden');
  assert.equal(cloud.requests.length, before);
  let held;
  const accepted = new Promise(resolve => { acceptedHeld = resolve; });
  const heldResponse = new Promise((resolve, reject) => {
    held = http.request({ host: '127.0.0.1', port: front.address().port, method: 'POST', path: `/api/internal/agent-llm/${key}/v1/chat/completions`, headers: { 'content-type': 'application/json' } }, reply => { reply.resume(); reply.on('end', () => resolve(reply.statusCode)); });
    held.on('error', reject); held.write('{"model":');
  });
  await accepted;
  await bridge.stop('cloud');
  await cloudTurn;
  held.end(JSON.stringify(FREELLM_MODELS[0]) + ',"messages":[]}');
  assert.equal(await heldResponse, 403, 'a delayed body cannot be forwarded after Stop');
  assert.equal(cloud.requests.length, before);
  assert.equal((await send(key, FREELLM_MODELS[0])).status, 404, 'closed as soon as the selected turn ends');
});
