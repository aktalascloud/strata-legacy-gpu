import { FREELLM_MODELS, FREELLM_URL } from './freellm.mjs';
import { isLanKobold } from './lan-kobold.mjs';
import { providerTarget } from './model-providers.mjs';

export function selectSwarmHelpers(value, providers) {
  if (!Array.isArray(value) || value.length < 1 || value.length > 4) {
    throw new Error('Choose up to four saved helpers.');
  }
  const chosen = new Set();
  return value.map(row => {
    const selection = { connectionId: row?.connectionId, modelId: row?.modelId };
    const { connection, model } = providers.resolve(selection);
    const free = connection.kind === 'provider' && connection.provider === 'freellm' &&
      connection.protocol === 'openai-chat' && connection.baseUrl === FREELLM_URL &&
      !connection.apiKey && FREELLM_MODELS.includes(model.id);
    const id = free ? model.id : JSON.stringify([connection.baseUrl, model.id]);
    if ((!free && !isLanKobold(connection)) || chosen.has(id)) {
      throw new Error('Choose distinct saved FreeLLM or KoboldCpp LAN models.');
    }
    chosen.add(id);
    return { selection, label: model.name || model.id, target: providerTarget(connection) };
  });
}

/** Only text drafted by the local planner can reach the helpers. */
export async function consultSwarm({ message, helpers, plan, providers, signal }) {
  signal.throwIfAborted();
  const response = await plan(message, helpers.length, signal);
  signal.throwIfAborted();
  let tasks;
  try { tasks = JSON.parse(response.trim().replace(/^```(?:json)?\s*|\s*```$/gi, '')); }
  catch { return []; }
  if (!Array.isArray(tasks) || tasks.length !== helpers.length ||
      tasks.some(task => typeof task !== 'string' || !task.trim() || task.length > 1600)) return [];

  const results = await Promise.allSettled(helpers.map(async ({ selection, label, target }, i) => {
    let answer = '';
    await providers.stream({
      selection, expectedTarget: target, message: tasks[i].trim(), thinking: 'off', maxTokens: 1024,
      systemPrompt: 'Give a concise advisory answer to the assigned text subtask.',
      signal: AbortSignal.any([signal, AbortSignal.timeout(90000)]),
      onFrame: frame => {
        if (frame.type === 'delta' && answer.length < 6000) answer += frame.text.slice(0, 6000 - answer.length);
      },
    });
    return { model: label, answer };
  }));
  signal.throwIfAborted();
  return results.flatMap(row => row.status === 'fulfilled' && row.value.answer ? [row.value] : []);
}
