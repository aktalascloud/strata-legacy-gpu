import test from 'node:test';
import assert from 'node:assert/strict';
import { cpSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { startScriptedWorker } from './helpers/scripted-worker.mjs';
import { createAgentBridge } from '../server/agent/agent-bridge.mjs';
import { resolveHarness } from '../server/agent/harness-runtime.mjs';

test('a persisted cloud child cannot resume, but its local sibling can', { skip: !resolveHarness({ env: process.env }).ok }, async t => {
  const directory = mkdtempSync(join(tmpdir(), 'strata-child-resume-'));
  const workspace = join(directory, 'workspace'); mkdirSync(workspace);
  // Make an isolated copy representing an older profile that permitted cloud helpers.
  const legacy = join(directory, 'legacy');
  cpSync(resolve('server'), legacy, { recursive: true });
  const profilePath = join(legacy, 'agent', 'profile.mjs');
  let profile = readFileSync(profilePath, 'utf8').replace(/\r\n/g, '\n');
  const add = '    privateSubagentProviders.add(route);\n';
  const localOnly = "routes.filter(r => r.kind === 'local').map(r => ({ provider: r.route, model: r.modelId, name: r.name, connection: r.connectionName, local: true }))";
  assert.ok(profile.includes(add) && profile.includes(localOnly));
  profile = profile.replace(add, '').replace(localOnly, "routes.map(r => ({ provider: r.route, model: r.modelId, name: r.name, connection: r.connectionName, local: r.kind === 'local' }))");
  writeFileSync(profilePath, profile);
  const { createAgentBridge: legacyBridge } = await import(pathToFileURL(join(legacy, 'agent', 'agent-bridge.mjs')).href);
  const local = await startScriptedWorker();
  const remote = await startScriptedWorker({ model: 'cloud-test' });
  const options = { dataDir: directory, env: process.env, startTimeoutMs: 90_000, localInstances: () => [{ id: 'local', label: 'Local', baseUrl: local.url, modelId: 'scripted-model', context: 32768, slots: 2 }], connections: () => [{ id: 'cloud', name: 'Cloud', baseUrl: remote.url, protocol: 'openai-chat', apiKey: 'test-key', models: [{ id: 'cloud-test', name: 'Cloud model', contextMax: 32768 }] }] };
  let first = legacyBridge(options), second;
  t.after(async () => { await first?.close(); await second?.close(); await local.close(); await remote.close(); try { rmSync(directory, { recursive: true, force: true, maxRetries: 3 }); } catch { /* Harness may retain temporary ACLs */ } });
  async function spawnChild(model, label) {
    const frames = [];
    const args = { description: label, prompt: 'SCRIPT:echo seed', model };
    await first.runTurn({ chatId: 'persisted', message: `SCRIPT:call subagent ${JSON.stringify(args)}`, workspacePath: workspace, mode: 'bypass', onFrame: f => frames.push(f) });
    const child = frames.find(frame => frame.type === 'agent' && frame.agent.name === label)?.agent.id;
    assert.ok(child, `persisted ${label} child must have an id`);
    return child;
  }
  const cloudChild = await spawnChild('Cloud model', 'Cloud child');
  const localChild = await spawnChild('Local', 'Local child');
  assert.ok(remote.requests.some(request => request.directive === 'echo'));
  await first.close(); first = null;
  const remoteBefore = remote.requests.length;
  second = createAgentBridge(options);
  await second.runTurn({ chatId: 'persisted', message: 'SCRIPT:echo resumed parent', workspacePath: workspace, mode: 'bypass', onFrame() {} });
  await assert.rejects(second.messageHelper({ chatId: 'persisted', helperId: cloudChild, text: 'SCRIPT:echo private' }));
  assert.equal(remote.requests.length, remoteBefore, 'the cloud child was not resumed');
  const localBefore = local.requests.length;
  const receipt = await second.messageHelper({ chatId: 'persisted', helperId: localChild, text: 'SCRIPT:echo local resumed' });
  assert.equal(receipt.ok, true);
  for (let i = 0; i < 80 && local.requests.length === localBefore; i++) await new Promise(resolve => setTimeout(resolve, 100));
  assert.ok(local.requests.length > localBefore, 'the persisted local sibling received the message');
  assert.equal(remote.requests.length, remoteBefore);
  const callMessage = async (child, message) => {
    const args = { agent_id: child, message };
    await second.runTurn({ chatId: 'persisted', message: `SCRIPT:call send_message ${JSON.stringify(args)}`, workspacePath: workspace, mode: 'bypass', onFrame() {} });
  };
  await callMessage(cloudChild, 'SCRIPT:echo private again');
  assert.equal(remote.requests.length, remoteBefore, 'model-facing send_message did not resume the cloud child');
  const echoBefore = local.requests.filter(request => request.directive === 'echo').length;
  await callMessage(localChild, 'SCRIPT:echo local again');
  for (let i = 0; i < 80 && local.requests.filter(request => request.directive === 'echo').length === echoBefore; i++) await new Promise(resolve => setTimeout(resolve, 100));
  assert.ok(local.requests.filter(request => request.directive === 'echo').length > echoBefore, 'model-facing send_message reached the local sibling');
  assert.equal(remote.requests.length, remoteBefore);
});
