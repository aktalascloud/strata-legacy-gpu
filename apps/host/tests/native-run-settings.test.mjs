import test from 'node:test';
import assert from 'node:assert/strict';
import { catalogIdForLocal, nativeRunSettings } from '../server/native-run-settings.mjs';

test('reports only the reviewed run settings and honors user argument overrides', () => {
  const cfg = { args: ['--max-context','131072','--kv','int8'], user_args: ['--max-context','262144','--kv','q4_0'], vision: { gpu: false, threads: 16 }, api_key: 'secret' };
  const actual = nativeRunSettings(cfg);
  assert.deepEqual(actual, { context: 262144, kv: 'q4_0', vision: 'cpu', visionThreads: 16 });
  assert.doesNotMatch(JSON.stringify(actual), /secret/);
  assert.deepEqual(nativeRunSettings({ args: [] }), { context: null, kv: null, vision: 'off', visionThreads: null });
});

test('the local Swift profile maps to the catalog template without changing its model identity', () => {
  assert.equal(catalogIdForLocal('swift-1.5-iq3-s', { model: 'swift-1.5-iq3-s' }), 'swift-iq3_s');
  assert.equal(catalogIdForLocal('swift-1.5-iq3-s', null), undefined);
  assert.equal(catalogIdForLocal('another', { model: 'swift-1.5-iq3-s' }), undefined);
});
