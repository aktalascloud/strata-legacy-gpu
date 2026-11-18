// Automatic compaction for a LOCAL model: it starts before the window is full, the chat goes on after it, and helpers get it too.
import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, rmSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { startScriptedWorker } from './helpers/scripted-worker.mjs';
import { createAgentBridge } from '../server/agent/agent-bridge.mjs';
import { resolveHarness } from '../server/agent/harness-runtime.mjs';
import { buildProfile, compactionHeadroom, localOutputBudget } from '../server/agent/profile.mjs';

const HARNESS = process.env.STRATA_HARNESS_DIR;
const skip = !HARNESS || !resolveHarness({ env: process.env }).ok ? 'STRATA_HARNESS_DIR is not set to a built Harness' : false;

test('the reply keeps 30 percent of the window (at most 32K) and compaction gets a headroom that fits, for every window size', () => {
  assert.equal(localOutputBudget(32768), 9830); assert.equal(localOutputBudget(262144), 32768); assert.equal(localOutputBudget(8192), 4096); assert.equal(localOutputBudget(undefined), 9830);
  for (const w of [8192, 16384, 32768, 65536, 131072, 262144, 1_000_000]) {
    const out = localOutputBudget(w), head = compactionHeadroom(w, out);
    const threshold = Math.floor(Math.min(w * 0.8, w - out - head));
    assert.ok(threshold > 0, `window ${w}: a positive start point (${threshold})`);
    assert.ok(threshold >= (w - out) * 0.5, `window ${w}: compaction starts after at least half of the room the conversation has (${threshold})`);
    assert.ok(Math.floor((w - out) * 0.16) < threshold, `window ${w}: the verbatim tail is smaller than the start point`);
  }
  const profile = buildProfile({ local: [{ id: 'a', modelId: 'm', baseUrl: 'http://x', context: 32768 }], connections: [] });
  assert.match(profile.patch, /"modelPolicies": \[\s*\{\s*"provider": "strata-local",\s*"model": "m",\s*"headroomTokens": 2867/);
});

test('a long chat on a small window compacts before it overflows, and the conversation goes on', { skip }, async (t) => {
  const worker = await startScriptedWorker({});
  const dir = mkdtempSync(join(tmpdir(), 'strata-compact-'));
  const ws = join(dir, 'ws'); mkdirSync(ws, { recursive: true });
  const bridge = createAgentBridge({ dataDir: dir, localInstances: () => [{ id: 'i', label: 'S', baseUrl: worker.url, modelId: 'scripted-model', context: 16384, slots: 2 }], connections: () => [], env: process.env, startTimeoutMs: 90_000 });
  t.after(async () => { await bridge.close(); await worker.close(); try { rmSync(dir, { recursive: true, force: true, maxRetries: 3 }); } catch { /* best effort */ } });
  const big = 'alpha '.repeat(1500);
  const replies = [];
  for (let i = 0; i < 6; i++) {
    const frames = [];
    await bridge.runTurn({ chatId: 'long', message: `SCRIPT:echo round${i} ${big}`, workspacePath: ws, mode: 'bypass', onFrame: f => frames.push(f) });
    replies.push(frames.filter(f => f.type === 'delta' && !f.noteReason).map(f => f.text).join('').slice(0, 12));
    assert.equal(frames.at(-1).type, 'done', `round ${i} ended normally`);
  }
  assert.ok(replies.every(r => /^round\d/.test(r)), 'every round was answered: ' + replies.join(' | '));
  const reqs = worker.requests;
  const summaries = reqs.filter(r => r.summary);
  assert.ok(summaries.length >= 1, 'the Harness asked for a summary of the old history');
  const answers = reqs.filter(r => !r.summary && r.toolNames.length);
  const peak = Math.max(...answers.map(r => r.promptChars));
  assert.ok(peak < 16384 * 4, `no request was bigger than the window (about ${Math.round(peak / 4)} tokens of 16384)`);
  const lastRoundPrompt = answers.at(-1).promptChars;
  assert.ok(lastRoundPrompt < answers[Math.min(4, answers.length - 1)].promptChars + 1, 'the prompt stopped growing');
});

test('configured recent messages survive an automatic compaction in the actual Harness', { skip, timeout: 120000 }, async t => {
  const worker = await startScriptedWorker({ window: 16384, charsPerToken: 4 });
  const dir = mkdtempSync(join(tmpdir(), 'strata-compact-policy-'));
  const ws = join(dir, 'ws'); mkdirSync(ws, { recursive: true });
  const bridge = createAgentBridge({ dataDir: dir, localInstances: () => [{ id: 'i', label: 'S', baseUrl: worker.url, modelId: 'scripted-model', context: 16384, slots: 2 }], connections: () => [], compactSettings: () => ({ thresholdTokens: 8500, keepMessages: 2 }), env: process.env, startTimeoutMs: 90000 });
  t.after(async () => { await bridge.close(); await worker.close(); try { rmSync(dir, { recursive: true, force: true, maxRetries: 3 }); } catch { /* best effort */ } });
  for (let i = 0; i < 7; i++) {
    const frames = [];
    try { await bridge.runTurn({ chatId: 'long', message: `SCRIPT:echo round${i} ${'alpha '.repeat(1100)}`, workspacePath: ws, mode: 'bypass', onFrame: f => frames.push(f) }); }
    catch (error) { await bridge.close(); let log = ''; try { log = readFileSync(join(dir, 'agent', 'harness.log'), 'utf8'); } catch {} throw new Error(`${error.message}\n${log}`, { cause: error }); }
    assert.equal(frames.at(-1).type, 'done', `round ${i}: ${JSON.stringify(frames.at(-1))}`);
  }
  assert.ok(worker.requests.some(r => r.summary), 'the real compaction engine summarized history');
  const last = worker.requests.filter(r => !r.summary && r.directive === 'echo').at(-1);
  const sent = JSON.parse(last.raw).messages;
  assert.ok(sent.some(m => m.role === 'user' && JSON.stringify(m.content).includes('SCRIPT:echo round6')), 'the current user message survives');
  assert.ok(sent.some(m => m.role === 'assistant' && JSON.stringify(m.content).includes('round5')), 'the previous assistant message survives verbatim');
});

test('a provider overflow retries the same step while protecting recent messages', { skip, timeout: 120000 }, async t => {
  const worker = await startScriptedWorker({ window: 16384, charsPerToken: 3, noCount: true });
  const dir = mkdtempSync(join(tmpdir(), 'strata-compact-overflow-'));
  const ws = join(dir, 'ws'); mkdirSync(ws, { recursive: true });
  const bridge = createAgentBridge({ dataDir: dir, localInstances: () => [{ id: 'i', label: 'S', baseUrl: worker.url, modelId: 'scripted-model', context: 32768, slots: 2 }], connections: () => [], compactSettings: () => ({ thresholdTokens: 30000, keepMessages: 2 }), env: process.env, startTimeoutMs: 90000 });
  t.after(async () => { await bridge.close(); await worker.close(); try { rmSync(dir, { recursive: true, force: true, maxRetries: 3 }); } catch {} });
  for (let i = 0; i < 6; i++) {
    const frames = [];
    await bridge.runTurn({ chatId: 'long', message: `SCRIPT:echo round${i} ${'q=0x1f ok;'.repeat(700)}`, workspacePath: ws, mode: 'bypass', onFrame: f => frames.push(f) });
    assert.equal(frames.at(-1).type, 'done', `round ${i}: ${JSON.stringify(frames.at(-1))}`);
  }
  const refused = worker.requests.findIndex(r => r.refused && r.directive === 'echo');
  assert.ok(refused >= 0, 'the provider really refused an answer request');
  const refusedMessage = [...worker.requests[refused].raw.matchAll(/SCRIPT:echo round\d+/g)].at(-1)?.[0];
  assert.ok(refusedMessage && worker.requests.slice(refused + 1).some(r => !r.refused && !r.summary && r.raw.includes(refusedMessage)), 'the same step was retried');
  assert.ok(worker.requests.some(r => r.summary), 'the older history was summarized');
  const last = worker.requests.filter(r => !r.summary && r.directive === 'echo').at(-1);
  const sent = JSON.parse(last.raw).messages;
  assert.ok(sent.some(m => m.role === 'user' && JSON.stringify(m.content).includes('SCRIPT:echo round5')) &&
    sent.some(m => m.role === 'assistant' && JSON.stringify(m.content).includes('round4')), 'the last two visible messages remain verbatim');
});

test('overflow does not discard a protected tail that cannot fit', { skip, timeout: 120000 }, async t => {
  const worker = await startScriptedWorker({ window: 8192, charsPerToken: 3, noCount: true });
  const dir = mkdtempSync(join(tmpdir(), 'strata-compact-protected-'));
  const ws = join(dir, 'ws'); mkdirSync(ws, { recursive: true });
  const bridge = createAgentBridge({ dataDir: dir, localInstances: () => [{ id: 'i', label: 'S', baseUrl: worker.url, modelId: 'scripted-model', context: 32768, slots: 2 }], connections: () => [], compactSettings: () => ({ thresholdTokens: 30000, keepMessages: 2 }), env: process.env, startTimeoutMs: 90000 });
  t.after(async () => { await bridge.close(); await worker.close(); try { rmSync(dir, { recursive: true, force: true, maxRetries: 3 }); } catch {} });
  const frames = [];
  await bridge.runTurn({ chatId: 'long', message: `SCRIPT:echo protected ${'q=0x1f ok;'.repeat(3000)}`, workspacePath: ws, mode: 'bypass', onFrame: f => frames.push(f) });
  assert.ok(worker.requests.some(r => r.refused), 'the provider rejected the oversized protected message');
  assert.ok(!worker.requests.some(r => r.summary), 'the protected message was not summarized away');
  assert.ok(frames.some(f => f.type === 'error'), 'the user sees the overflow');
});

test('overflow retry keeps a long protected tool result unpruned', { skip, timeout: 120000 }, async t => {
  const worker = await startScriptedWorker({ noCount: true, overflowLongToolOnce: true });
  const dir = mkdtempSync(join(tmpdir(), 'strata-compact-tool-'));
  const ws = join(dir, 'ws'); mkdirSync(ws, { recursive: true });
  const file = join(ws, 'long.txt');
  writeFileSync(file, `START_PROTECTED\n${('protected '.repeat(10) + '\n').repeat(110)}END_PROTECTED\n`);
  const bridge = createAgentBridge({ dataDir: dir, localInstances: () => [{ id: 'i', label: 'S', baseUrl: worker.url, modelId: 'scripted-model', context: 32768, slots: 2 }], connections: () => [], compactSettings: () => ({ thresholdTokens: 30000, keepMessages: 2 }), env: process.env, startTimeoutMs: 90000 });
  t.after(async () => { await bridge.close(); await worker.close(); try { rmSync(dir, { recursive: true, force: true, maxRetries: 3 }); } catch {} });
  const send = async message => { const frames = []; await bridge.runTurn({ chatId: 'long', message, workspacePath: ws, mode: 'bypass', onFrame: f => frames.push(f) }); return frames; };
  assert.equal((await send('SCRIPT:echo old conversation')).at(-1).type, 'done');
  assert.equal((await send('SCRIPT:echo another old message')).at(-1).type, 'done');
  const result = await send(`SCRIPT:read ${file}`);
  assert.equal(result.at(-1).type, 'done', JSON.stringify(result.at(-1)));
  const refused = worker.requests.findIndex(r => r.refused === 'long-tool');
  assert.ok(refused >= 0, 'the provider rejected the step with the actual long tool result: ' + JSON.stringify(worker.requests.map(r => ({ directive: r.directive, roles: JSON.parse(r.raw).messages.map(m => [m.role, JSON.stringify(m.content).length]) }))));
  const toolContents = r => JSON.parse(r.raw).messages.filter(m => m.role === 'tool').map(m => JSON.stringify(m.content)).find(s => s.includes('START_PROTECTED'));
  const original = toolContents(worker.requests[refused]);
  assert.ok(original?.includes('END_PROTECTED') && original.length > 8192, 'the original result was long and complete');
  const retried = worker.requests.slice(refused + 1).find(r => !r.refused && !r.summary && toolContents(r));
  assert.ok(retried, 'the same step was retried with its tool result');
  assert.equal(toolContents(retried), original, 'the protected tool result was not pruned');
});
