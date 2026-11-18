import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { FREELLM_MODELS, FREELLM_URL } from '../server/freellm.mjs';
import { consultSwarm, selectSwarmHelpers } from '../server/freellm-swarm.mjs';
import { isLanKobold } from '../server/lan-kobold.mjs';
import { createModelProviders } from '../server/model-providers.mjs';

const selection = FREELLM_MODELS.map(modelId => ({ connectionId: 'kilo', modelId }));
const resolve = row => ({
  connection: { kind: 'provider', provider: 'freellm', protocol: 'openai-chat', baseUrl: FREELLM_URL },
  model: { id: row.modelId, name: row.modelId },
});

test('the swarm targets saved KoboldCpp LAN models without requiring Kilo', async () => {
  const lan = { connectionId: 'lan', modelId: 'koboldcpp/local' };
  const connection = { provider: 'koboldcpp-lan', baseUrl: 'http://192.168.0.9:5001/v1', protocol: 'openai-chat' };
  assert.equal(isLanKobold(connection), true);
  for (const baseUrl of ['https://example.com/v1', 'http://8.8.8.8/v1', 'http://192.168.0.9/admin',
    'http://192.168.0.9/v1?forward=https://example.com']) {
    assert.equal(isLanKobold({ ...connection, baseUrl }), false);
  }
  const helpers = selectSwarmHelpers([selection[0], lan], {
    resolve: row => row.connectionId === 'lan' ? { connection, model: { id: row.modelId } } : resolve(row),
  });
  assert.deepEqual(helpers.map(row => row.selection), [selection[0], lan]);
});

test('a LAN connection can wait for its real model before appearing in the picker', async t => {
  const directory = mkdtempSync(join(tmpdir(), 'strata-lan-model-'));
  t.after(() => rmSync(directory, { recursive: true, force: true }));
  let discovered;
  const done = new Promise(resolve => { discovered = resolve; });
  const manager = createModelProviders({
    directory,
    changed: value => { const model = value.connections[0]?.models?.[0]; if (model) discovered(model); },
    fetchImpl: async (url, options) => {
      assert.equal(url, 'http://192.168.0.9:5001/v1/models');
      assert.equal(options.redirect, 'error');
      return Response.json({ data: [{ id: 'inactive' }, { id: 'koboldcpp/the-real-model' }] });
    },
  });
  const saved = manager.save({ provider: 'koboldcpp-lan', baseUrl: 'http://192.168.0.9:5001/v1/', models: [] });
  assert.deepEqual(saved.connections[0].models, []);
  manager.discoverPendingLan();
  assert.equal((await done).id, 'koboldcpp/the-real-model');
  assert.equal(manager.list().connections[0].models.length, 1);
});

test('an edited connection cannot redirect a subtask while Swift is planning', async t => {
  const directory = mkdtempSync(join(tmpdir(), 'strata-swarm-target-'));
  t.after(() => rmSync(directory, { recursive: true, force: true }));
  let fetches = 0;
  const manager = createModelProviders({ directory, fetchImpl: async () => { fetches++; throw new Error('unexpected request'); } });
  const models = [{ id: 'koboldcpp/local' }];
  const { connections: [saved] } = manager.save({ provider: 'koboldcpp-lan', baseUrl: 'http://192.168.0.9:5001/v1', models });
  const helpers = selectSwarmHelpers([{ connectionId: saved.id, modelId: models[0].id }], manager);
  const notes = await consultSwarm({
    message: 'question', helpers, providers: manager, signal: AbortSignal.timeout(1000),
    plan: async () => {
      manager.save({ id: saved.id, kind: 'custom', name: saved.name, protocol: 'openai-chat', baseUrl: 'https://example.test/v1', models });
      return '["private subtask"]';
    },
  });
  assert.deepEqual(notes, []);
  assert.equal(fetches, 0);
});

test('swarm accepts distinct saved FreeLLM models at the official endpoint only', () => {
  assert.equal(selectSwarmHelpers(selection, { resolve }).length, 2);
  assert.throws(() => selectSwarmHelpers([selection[0], selection[0]], { resolve }), /distinct/);
  assert.throws(() => selectSwarmHelpers([{ connectionId: 'kilo', modelId: 'paid' }], { resolve }), /distinct/);
  for (const fields of [{ provider: 'custom' }, { baseUrl: 'http://example.test' }, { apiKey: 'key' }]) {
    assert.throws(() => selectSwarmHelpers(selection, {
      resolve: row => ({ ...resolve(row), connection: { ...resolve(row).connection, ...fields } }),
    }), /distinct/);
  }
});

test('the local planner makes separate text subtasks and both helpers run concurrently', async () => {
  const helpers = selectSwarmHelpers(selection, { resolve });
  const calls = [];
  let schedule;
  const scheduled = new Promise(resolve => { schedule = resolve; });
  const providers = { stream: async ({ message, selection, onFrame, ...extra }) => {
    assert.equal(extra.history, undefined);
    assert.equal(extra.images, undefined);
    assert.equal(extra.maxTokens, 1024);
    calls.push(message);
    if (calls.length === 2) schedule();
    await scheduled;
    onFrame({ type: 'delta', text: 'answer from ' + selection.modelId });
  } };
  const notes = await consultSwarm({
    message: 'Current user message', helpers, providers, signal: AbortSignal.timeout(1000),
    plan: async (message, count) => {
      assert.equal(message, 'Current user message');
      assert.equal(count, 2);
      return '["Check cost","Check lifespan"]';
    },
  });
  assert.deepEqual(calls, ['Check cost', 'Check lifespan']);
  assert.equal(notes.length, 2);
});

test('an invalid or cancelled local plan makes no cloud call', async () => {
  const helpers = selectSwarmHelpers(selection, { resolve });
  const providers = { stream: async () => assert.fail('unapproved helper request') };
  const controller = new AbortController();
  const args = { message: 'question', helpers, providers, signal: controller.signal };
  assert.deepEqual(await consultSwarm({ ...args, plan: async () => 'not JSON' }), []);
  await assert.rejects(consultSwarm({ ...args, plan: async () => {
    controller.abort();
    return '["first","second"]';
  } }), { name: 'AbortError' });
});
