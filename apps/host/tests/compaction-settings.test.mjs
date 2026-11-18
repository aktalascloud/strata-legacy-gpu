import { test } from 'node:test';
import assert from 'node:assert/strict';
import { compactPolicy, compactionSettings, protectedCompactionRange } from '../server/agent/compaction-settings.mjs';
import { buildProfile } from '../server/agent/profile.mjs';

test('settings are bounded whole numbers and default to existing automatic behavior', () => {
  assert.deepEqual(compactionSettings(), { thresholdTokens: 0, keepMessages: 0 });
  for (const input of [{ thresholdTokens: -1 }, { thresholdTokens: 1.2 }, { keepMessages: 1001 }, { keepMessages: '2' }])
    assert.throws(() => compactionSettings(input));
  assert.deepEqual(compactPolicy('p', 'm', 8192, 4096, 512, { thresholdTokens: 7000, keepMessages: 3 }),
    { provider: 'p', model: 'm', headroomTokens: 512, thresholdRatio: 7000 / 8192, retainTokens: 0 });
  assert.equal(compactPolicy('p', 'm', 8192, 4096, 512, { thresholdTokens: 90000 }).thresholdRatio, 1);
});

function session(events) {
  return { surface: { nodes: events.map((_, i) => i + 1) }, eventAt: seq => events[seq - 1] };
}
const user = text => ({ type: 'user/message', data: { role: 'user', source: { kind: 'user' }, content: [{ type: 'text', text }] } });
const assistant = text => ({ type: 'assistant/message', data: { message: { content: [{ type: 'text', text }] } } });
const toolCall = { type: 'assistant/message', data: { message: { content: [{ type: 'tool-call' }] } } };
const toolResult = { type: 'tool/result' };
test('recent visible messages survive and a tool call is not separated from its result', () => {
  const s = session([user('old'), assistant('old'), user('new'), toolCall, toolResult, assistant('new')]);
  assert.deepEqual(protectedCompactionRange(s, 1, 6, 2, () => true), { start: 1, end: 2 });
  const t = session([user('old'), toolCall, toolResult, assistant('new')]);
  assert.deepEqual(protectedCompactionRange(t, 1, 4, 1, (_, seq) => seq !== 4 && seq !== 3), { start: 1, end: 1 });
  assert.throws(() => protectedCompactionRange(s, 1, 6, 10, () => true), /no safe history/);
  assert.deepEqual(protectedCompactionRange(s, 1, 6, 0, () => true), { start: 1, end: 6 });
});

test('runtime snapshots and compact checkpoints do not consume the visible-message count', () => {
  const injected = kind => ({ type: 'user/message', data: { role: 'user', source: { kind }, content: [{ type: 'text', text: 'internal' }] } });
  const s = session([user('old'), assistant('old'), user('new'), injected('runtime-context'), injected('compact-checkpoint'), assistant('new'), injected('runtime-context')]);
  assert.deepEqual(protectedCompactionRange(s, 1, 7, 2, () => true), { start: 1, end: 2 });
  const bad = session([user('old'), { type: 'user/message', data: { role: 'user' } }]);
  assert.throws(() => protectedCompactionRange(bad, 1, 2, 1, () => true), /no valid source/);
});

test('each model gets its own window-aware policy and settings changes restart the agent at idle', () => {
  const local = [{ id: 'one', modelId: 'swift', baseUrl: 'http://127.0.0.1:1/v1', context: 262144 }];
  const baseline = buildProfile({ local });
  const next = buildProfile({ local, compact: { thresholdTokens: 60000, keepMessages: 6 } });
  const rows = JSON.parse(next.patch.split('\n').slice(1).join('\n').replace(/!!js process\.env\.[A-Za-z0-9_]+/g, '"masked"'));
  const preset = rows.find(row => row.id === 'preset-standard');
  const group = preset.config.plugins.find(row => row.id === 'compaction');
  const basic = group.config.find(row => row.id === 'compaction-basic');
  assert.equal(group.config.some(row => row.id === 'tool-result-pruner'), false, 'protected tool results are never pruned');
  const baseRows = JSON.parse(baseline.patch.split('\n').slice(1).join('\n').replace(/!!js process\.env\.[A-Za-z0-9_]+/g, '"masked"'));
  assert.equal(baseRows.find(row => row.id === 'preset-standard').config.plugins.find(row => row.id === 'compaction').config.some(row => row.id === 'tool-result-pruner'), true, 'default profile keeps upstream pruning');
  assert.match(basic.name, /strata-compaction\.mjs$/);
  assert.equal(basic.config.modelPolicies[0].thresholdRatio, 60000 / 262144);
  assert.equal(basic.config.modelPolicies[0].retainTokens, 0);
  assert.equal(next.env.STRATA_COMPACTION_KEEP_MESSAGES, '6');
  assert.notEqual(next.toolsSignature, baseline.toolsSignature);
});
