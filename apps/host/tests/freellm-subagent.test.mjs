import test from 'node:test';
import assert from 'node:assert/strict';
import { buildProfile } from '../server/agent/profile.mjs';
import { apply } from '../server/agent/plugins/strata-models.mjs';
import { FREELLM_MODELS, FREELLM_URL } from '../server/freellm.mjs';
import { createAgentBridge } from '../server/agent/agent-bridge.mjs';
import { createLlmProxy } from '../server/agent/llm-shape.mjs';
import { resolveHarness } from '../server/agent/harness-runtime.mjs';
import { startScriptedWorker } from './helpers/scripted-worker.mjs';
import { mkdirSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import http from 'node:http';

const cloud = { id: 'free', provider: 'freellm', name: 'FreeLLM', baseUrl: FREELLM_URL, protocol: 'openai-chat', apiKey: '', models: [{ id: FREELLM_MODELS[0], contextMax: 1000000, maxOutput: 65536 }] };
const local = { id: 'swift', label: 'Swift', baseUrl: 'http://127.0.0.1:8093/v1', modelId: 'swift-1.5-iq3-s', context: 262144 };
const otherCloud = { id: 'openai', provider: 'openai', name: 'OpenAI', baseUrl: 'https://api.openai.com/v1', protocol: 'openai-chat', apiKey: 'test-key', models: [{ id: 'other-cloud-model', contextMax: 64000 }] };
const entries = profile => JSON.parse(profile.patch.slice(profile.patch.indexOf('[')));
function setup(includeLocal = true) {
  const profile = buildProfile({ local: includeLocal ? [local] : [], connections: [cloud, otherCloud], proxyBase: 'http://127.0.0.1:9999/proxy', proxyNonce: 'testnonce' });
  const items = entries(profile);
  const settings = items.find(item => item.id === 'subagent-model-selection-settings');
  const plugin = items.flatMap(item => item.insert ?? []).find(item => item.id === 'strata-models');
  const calls = [];
  const tool = { description: '', parameters: { properties: { model: {}, provider: {} } }, execute(args) { calls.push(args); return 'ok'; } };
  apply({ get: () => ({ list: () => [{}] }), tools: { get: name => name === 'subagent' ? tool : null }, on() {} }, plugin.config);
  return { profile, settings, plugin, calls, tool };
}
const execute = (tool, args, provider, optionsProvider = provider) => tool.execute(args, { agent: { options: { provider: optionsProvider }, session: { requestHeader: () => ({ config: { provider } }) } } });

test('saved FreeLLM is never offered to helpers when Swift is active', () => {
  const { profile, settings, plugin, tool, calls } = setup();
  const free = profile.routes.find(route => route.connectionId === 'free');
  assert.ok(free, 'the selected main agent still has a FreeLLM route');
  assert.deepEqual(settings.config.allowedModels, [{ provider: 'strata-local', model: local.modelId }]);
  const paid = profile.routes.find(route => route.connectionId === 'openai');
  assert.ok(paid, 'the explicitly selected main OpenAI route remains available');
  assert.deepEqual(plugin.config.blockedInheritedProviders, [free.route, paid.route]);
  assert.equal(plugin.config.routes.length, 1);
  assert.throws(() => execute(tool, { model: FREELLM_MODELS[0] }, 'strata-local'), /No model is called/);
  assert.throws(() => execute(tool, { model: 'other-cloud-model' }, 'strata-local'), /No model is called/);
  assert.throws(() => execute(tool, {}, free.route, 'strata-local'), /cannot be inherited/);
  assert.throws(() => execute(tool, {}, paid.route, 'strata-local'), /cannot be inherited/);
  assert.throws(() => execute(tool, { reasoning_effort: 'high' }, free.route), /cannot be inherited/);
  assert.throws(() => execute(tool, {}, undefined), /cannot be inherited/);
  assert.equal(execute(tool, {}, 'strata-local'), 'ok');
  assert.equal(execute(tool, { model: 'local' }, free.route), 'ok');
  assert.deepEqual(calls.at(-1), { provider: 'strata-local', model: local.modelId });
});

test('a remote main agent stays usable when there is no local helper route', () => {
  const { profile, settings, plugin, tool } = setup(false);
  const free = profile.routes.find(route => route.connectionId === 'free');
  const paid = profile.routes.find(route => route.connectionId === 'openai');
  assert.ok(free);
  assert.equal(settings, undefined, 'Harness requires a nonempty selectable allowlist');
  assert.deepEqual(plugin.config.routes, []);
  assert.throws(() => execute(tool, {}, free.route), /cannot be inherited/);
  assert.throws(() => execute(tool, {}, paid.route), /cannot be inherited/);
  assert.throws(() => execute(tool, { provider: free.route, model: FREELLM_MODELS[0] }, free.route), /No other model/);
});

test('workflow fails closed when the delegation service cannot be guarded', () => {
  const workflow = { execute() { throw new Error('must not run'); } };
  apply({ get: name => name === 'agents' ? { list: () => [{}] } : undefined, tools: { get: name => name === 'workflow' ? workflow : null }, on() {} }, { blockedInheritedProviders: ['api-cloud'], routes: [] });
  assert.throws(() => workflow.execute(), /unavailable while cloud models are connected/);
});

test('the shared delegation guard accepts local routes and is removed on plugin disposal', () => {
  const calls = [];
  const service = { startActivation(spec) { calls.push(spec); return 'started'; }, sendMessage() {}, [Symbol.for('dsh.subagent.deliverPrompt')]() {} };
  const agents = { get() {}, resume() {} };
  const disposers = [];
  apply({ subagents: service, agents, get: () => ({ list: () => [] }), tools: { get: () => null }, on() {}, effect(register) { disposers.push(register()); } }, { blockedInheritedProviders: ['api-cloud'], localDelegationRoutes: [{ provider: 'strata-local', model: 'swift' }], routes: [] });
  const spec = (parent, override) => ({ request: { parent: { options: parent }, ...(override ? { agentOptions: override } : {}) } });
  assert.equal(service.startActivation(spec({ provider: 'strata-local', model: 'swift' })), 'started');
  assert.throws(() => service.startActivation(spec({ provider: 'strata-local', model: 'swift' }, { provider: 'api-cloud', model: 'remote' })), /local models only/);
  assert.throws(() => service.startActivation(spec({ provider: 'api-cloud', model: 'remote' })), /local models only/);
  assert.equal(calls.length, 1);
  for (const dispose of disposers.reverse()) dispose();
  assert.equal(service.startActivation(spec({ provider: 'api-cloud', model: 'remote' })), 'started');
});

test('existing child delivery and cold resume require a proven local route', () => {
  const delivery = Symbol.for('dsh.subagent.deliverPrompt');
  const calls = [];
  const service = { startActivation() {}, sendMessage(...args) { calls.push(args); }, [delivery](...args) { calls.push(args); } };
  const live = new Map([['local', { options: { provider: 'strata-local', model: 'swift' } }], ['cloud', { options: { provider: 'api-cloud', model: 'remote' } }]]);
  const agents = { get(id) { return live.get(id); }, resume(options) { calls.push(options); } };
  apply({ subagents: service, agents, get: () => ({ list: () => [] }), tools: { get: () => null }, on() {}, effect(register) { register(); } }, { blockedInheritedProviders: ['api-cloud'], localDelegationRoutes: [{ provider: 'strata-local', model: 'swift' }], routes: [] });
  const sender = { session: { header: { parentSession: 'parent' } } };
  service.sendMessage(sender, 'parent', []);
  service.sendMessage(sender, 'local', []);
  assert.throws(() => service.sendMessage(sender, 'cloud', []), /verified local/);
  service[delivery](sender, 'local', []);
  assert.throws(() => service[delivery](sender, 'cloud', []), /verified local/);
  agents.resume({ parentAgent: sender, agentOptions: { provider: 'strata-local', model: 'swift' } });
  assert.throws(() => agents.resume({ parentAgent: sender, agentOptions: { provider: 'api-cloud', model: 'remote' } }), /verified local/);
  assert.throws(() => agents.resume({ parentAgent: sender, agentOptions: {} }), /verified local/);
  agents.resume({ agentOptions: { provider: 'api-cloud', model: 'remote' } });
  assert.equal(calls.length, 5, 'main chat and local deliveries still work');
});

test('real Harness keeps helpers local and blocks inheritance of cloud models', { skip: !resolveHarness({ env: process.env }).ok }, async t => {
  const localWorker = await startScriptedWorker();
  const remoteWorker = await startScriptedWorker({ model: FREELLM_MODELS[0] });
  const otherWorker = await startScriptedWorker({ model: 'other-cloud-model' });
  const directory = mkdtempSync(join(tmpdir(), 'strata-free-private-'));
  const workspace = join(directory, 'workspace'); mkdirSync(workspace);
  let bridge;
  const proxy = createLlmProxy({ targetOf: key => { const target = bridge.llmTarget(key); return target?.anonymousFree ? { ...target, base: remoteWorker.url } : target; }, samplingNow: () => null });
  const front = http.createServer((req, res) => { const match = /^\/api\/internal\/agent-llm\/([^/]+)(\/.*)$/.exec(req.url); if (!match) { res.writeHead(404); return res.end(); } proxy(req, res, match[1], match[2]); });
  await new Promise(resolve => front.listen(0, '127.0.0.1', resolve));
  bridge = createAgentBridge({ dataDir: directory, env: process.env, startTimeoutMs: 90_000, localInstances: () => [{ ...local, id: 'swift', baseUrl: localWorker.url, modelId: 'scripted-model', slots: 2 }], connections: () => [cloud, { ...otherCloud, baseUrl: otherWorker.url }], proxyBase: `http://127.0.0.1:${front.address().port}/api/internal/agent-llm` });
  t.after(async () => { await bridge.close(); await localWorker.close(); await remoteWorker.close(); await otherWorker.close(); await new Promise(resolve => front.close(resolve)); try { rmSync(directory, { recursive: true, force: true, maxRetries: 3 }); } catch { /* Harness may retain temporary ACLs */ } });
  const ask = async (id, choice, args, tool = 'subagent', extra = {}) => { const frames = []; await bridge.runTurn({ chatId: id, choice, message: `SCRIPT:call ${tool} ${JSON.stringify(args)}`, workspacePath: workspace, mode: 'bypass', ...extra, onFrame: frame => frames.push(frame) }); return frames.filter(f => f.type === 'delta').map(f => f.text).join(''); };
  const denied = await ask('local-private', { instanceId: 'swift' }, { description: 'Cloud', prompt: 'SCRIPT:echo private', model: FREELLM_MODELS[0] });
  assert.match(denied, /No model is called/);
  assert.equal(remoteWorker.requests.length, 0, 'the local chat did not send a helper to FreeLLM');
  const deniedOther = await ask('local-private-other', { instanceId: 'swift' }, { description: 'Cloud', prompt: 'SCRIPT:echo private', model: 'other-cloud-model' });
  assert.match(deniedOther, /No model is called/);
  assert.equal(otherWorker.requests.length, 0, 'the local chat did not send a helper to another provider');
  const inherited = await ask('cloud-private', { connectionId: 'free', modelId: FREELLM_MODELS[0] }, { description: 'Helper', prompt: 'SCRIPT:echo private' });
  assert.match(inherited, /cannot be inherited/);
  assert.equal(remoteWorker.requests.some(request => request.directive === 'echo'), false, 'the FreeLLM main agent did not start an implicit cloud helper');
  const inheritedOther = await ask('other-private', { connectionId: 'openai', modelId: 'other-cloud-model' }, { description: 'Helper', prompt: 'SCRIPT:echo private' });
  assert.match(inheritedOther, /cannot be inherited/);
  assert.equal(otherWorker.requests.some(request => request.directive === 'echo'), false, 'another remote main agent did not start an implicit cloud helper');
  const fork = await ask('cloud-fork', { connectionId: 'free', modelId: FREELLM_MODELS[0] }, { description: 'Fork', prompt: 'SCRIPT:echo private' }, 'subagent_fork');
  assert.match(fork, /cannot be inherited/);
  const localForkBefore = localWorker.requests.filter(request => request.directive === 'echo').length;
  await ask('local-fork', { instanceId: 'swift' }, { description: 'Fork', prompt: 'SCRIPT:echo local fork' }, 'subagent_fork');
  for (let i = 0; i < 80 && localWorker.requests.filter(request => request.directive === 'echo').length === localForkBefore; i++) await new Promise(resolve => setTimeout(resolve, 100));
  assert.ok(localWorker.requests.filter(request => request.directive === 'echo').length > localForkBefore, 'local fork remains usable');
  const meta = { name: 'privacy-check', description: 'Check local and remote workflow routes.' };
  const localBefore = localWorker.requests.filter(request => request.directive === 'echo').length;
  const localFlow = await ask('workflow-local', { instanceId: 'swift' }, { meta, script: 'return await agent("SCRIPT:echo local")' }, 'workflow');
  assert.doesNotMatch(localFlow, /Error/);
  assert.ok(localWorker.requests.filter(request => request.directive === 'echo').length > localBefore, 'local workflow really ran its helper');
  const shapedBefore = localWorker.requests.filter(request => request.directive === 'echo').length;
  const shapedFlow = await ask('workflow-local-shaped', { instanceId: 'swift' }, { meta, script: 'return await agent("SCRIPT:echo local")' }, 'workflow', { thinking: 'high', thinkingBudget: 8192 });
  assert.doesNotMatch(shapedFlow, /Error/);
  assert.ok(localWorker.requests.filter(request => request.directive === 'echo').length > shapedBefore, 'local workflow works with a shaped route');
  const remoteBefore = otherWorker.requests.length;
  await ask('workflow-deny', { instanceId: 'swift' }, { meta, script: 'return await agent("SCRIPT:echo private", { provider: "api-openai", model: "other-cloud-model" })' }, 'workflow');
  assert.equal(otherWorker.requests.length, remoteBefore, 'workflow did not reach the remote model');
  await ask('workflow-deny-shaped', { instanceId: 'swift' }, { meta, script: 'return await agent("SCRIPT:echo private", { provider: "api-openai~s0", model: "other-cloud-model" })' }, 'workflow');
  assert.equal(otherWorker.requests.length, remoteBefore, 'workflow did not reach a shaped remote alias');
  const cloudBefore = remoteWorker.requests.filter(request => request.directive === 'echo').length;
  await ask('workflow-inherit', { connectionId: 'free', modelId: FREELLM_MODELS[0] }, { meta, script: 'return await agent("SCRIPT:echo private")' }, 'workflow');
  assert.equal(remoteWorker.requests.filter(request => request.directive === 'echo').length, cloudBefore, 'workflow did not inherit the remote main model');
});
