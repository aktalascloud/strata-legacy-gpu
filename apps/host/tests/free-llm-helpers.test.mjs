import test from 'node:test';
import assert from 'node:assert/strict';
import { build } from 'esbuild';

const bundled = await build({ entryPoints: ['src/lib/free-llm-helpers.ts'], bundle: true, write: false, format: 'esm' });
const { availableFreeLlmHelpers, canSendToFreeLlm, selectedFreeLlmHelpers } = await import(`data:text/javascript;base64,${Buffer.from(bundled.outputFiles[0].text).toString('base64')}`);

test('consent stays off by default and refers to exact saved anonymous models', () => {
  const modelId = 'nvidia/nemotron-3-ultra-550b-a55b:free';
  const connection = { id: 'allowed', kind: 'provider', provider: 'freellm', baseUrl: 'https://ai-gateway.kilo.ai/api/v1', protocol: 'openai-chat', apiKeySet: false, models: [{ id: modelId, name: 'Nemotron' }, { id: 'paid', name: 'Other' }] };
  const providers = { connections: [{ ...connection, id: 'loopback', baseUrl: 'http://127.0.0.1' }, { ...connection, id: 'authenticated', apiKeySet: true }, connection] };
  const allowed = { connectionId: 'allowed', modelId };
  assert.deepEqual(availableFreeLlmHelpers(providers), [{ ...allowed, name: 'Nemotron', route: 'cloud' }]);
  assert.deepEqual(selectedFreeLlmHelpers(providers), []);
  assert.deepEqual(selectedFreeLlmHelpers(providers, [allowed, allowed, { connectionId: 'loopback', modelId }, { connectionId: 'allowed', modelId: 'paid' }]), [allowed]);
  assert.deepEqual(selectedFreeLlmHelpers(null, [allowed]), []);
});

test('registered LAN models can join the same selection up to its four-model limit', () => {
  const models = Array.from({ length: 6 }, (_, n) => ({ id: `lan-${n}`, name: `Model ${n}` }));
  const providers = { connections: [{ id: 'lan', kind: 'provider', provider: 'koboldcpp-lan', protocol: 'openai-chat', models }] };
  assert.deepEqual(selectedFreeLlmHelpers(providers, models.map(m => ({ connectionId: 'lan', modelId: m.id }))), models.slice(0, 4).map(m => ({ connectionId: 'lan', modelId: m.id })));
});

test('only an explicit composer text message can use cloud helpers', () => {
  assert.equal(canSendToFreeLlm('Investigate the two design choices', { direct: true }), true);
  assert.equal(canSendToFreeLlm('queued or automatic turn', { direct: false }), false);
  assert.equal(canSendToFreeLlm('/plan review', { direct: true }), false);
  assert.equal(canSendToFreeLlm('Read the quote', { direct: true, hasQuotes: true }), false);
  assert.equal(canSendToFreeLlm('Read this image', { direct: true, hasImages: true }), false);
  assert.equal(canSendToFreeLlm('Review this\n\nAttached budget.csv\n\ncontents', { direct: true }), false);
});
