/**
 * Helper agents on a model the person names: the Harness `subagent` tool with a forgiving model choice.
 *
 * The pinned Harness's `subagent` tool takes an exact `provider` route key and model id, and its discovery tool lists them as
 * `api-1b2c3d4e-5f/deepseek/deepseek-v3.2`. Nobody (and no small local model) can guess that from "ask DeepSeek". This plugin keeps the
 * Harness's tool and its checks and changes three things at the seam where the tool is called:
 *
 *   - the choice: the model id, `provider/id`, the name in the model picker, or "the local model" (any letters) is turned into the route
 *     the Harness needs; a close guess is not started but answered with "Did you mean ...?" for the person to confirm; nothing that fits
 *     is answered with the plain list of models that can be used (server/agent/model-routes.mjs);
 *   - the words the assistant reads: the tool says when to use it ("ask a subagent", "ask model X") and that the model must never be looked for
 *     with shell commands or in the environment;
 *   - the discovery tool lists the models by the names the person knows.
 *
 * It rewrites no Harness file: the two tool definitions the Harness registers for each chat are wrapped in place (their `execute` and their
 * text), once each. A Harness update that renames them leaves the tools as they were and the test that runs the real Harness fails.
 *
 * Plain ESM, loaded by absolute path like strata-gate.mjs. `config.routes` is the table the profile wrote (model-routes.mjs documents a route).
 */
import { modelProblem, resolveModel, routeList } from '../model-routes.mjs';

export const name = 'strata-models';
export const inject = ['tools', 'subagents', 'agents'];

/** What the assistant is told in the tool's own text, so every model (a small local one and a hosted one alike) knows when and how. */
export const SUBAGENT_GUIDANCE = ' Use this tool whenever the person asks you to ask a subagent, a helper or another model ("ask a subagent", "ask DeepSeek", "use the local model", "ask model X"): start it with this tool and do not look for the model yourself with shell commands, in the environment or on this computer. To use a particular model, give `model` as its name or id (for example "DeepSeek V3.2" or "deepseek/deepseek-v3.2", or "local" for the model running on this computer); `provider` is optional. `list_subagent_models` shows what can be used. After starting a helper, do not wait with sleep or commands: end your turn and its answer arrives as a new message.';
const MODEL_WORDS = 'The model to use for the helper: its name as the person knows it ("DeepSeek V3.2"), its id ("deepseek/deepseek-v3.2") or "local" for the model running on this computer. Omit it to use this chat\'s model.';
const PROVIDER_WORDS = 'Optional: the connection the model belongs to ("OpenRouter"). Usually the model alone is enough.';

const wrapped = new WeakSet();

/** The two wrappers' behaviour, apart from the Harness objects (the tests call these directly). */
export function subagentArgs(routes, args) {
  const result = resolveModel(routes, args ?? {});
  if (result.status !== 'exact') return { ok: result.status === 'inherit', args };
  const { provider, model } = result.route;
  return { ok: true, args: { ...args, provider, model } };
}

export function apply(ctx, config = {}) {
  const routes = Array.isArray(config.routes) ? config.routes : [];
  const blocked = new Set(Array.isArray(config.blockedInheritedProviders) ? config.blockedInheritedProviders : []);
  const allowed = Array.isArray(config.localDelegationRoutes) ? config.localDelegationRoutes : [];
  let guarded = false;
  let resumeGuarded = false;
  let messagingGuarded = false;
  if (blocked.size) {
    try {
      const service = ctx.subagents ?? ctx.get('subagents');
      const agents = ctx.agents ?? ctx.get('agents');
      const permits = (provider, model) => allowed.some(route => route.provider === provider && route.model === model);
      const install = (object, key, wrapper) => {
        const original = object?.[key];
        if (typeof original !== 'function') return false;
        const guard = wrapper(original);
        object[key] = guard;
        const installed = Object.getOwnPropertyDescriptor(object, key)?.value === guard;
        if (installed && ctx.effect) ctx.effect(() => () => { if (Object.getOwnPropertyDescriptor(object, key)?.value === guard) object[key] = original; });
        return installed;
      };
      resumeGuarded = install(agents, 'resume', original => function(options) {
        if (options?.parentAgent && !permits(options.agentOptions?.provider, options.agentOptions?.model)) throw new Error('Only a verified local helper can be resumed.');
        return original.call(this, options);
      });
      const checkTarget = (parent, targetId) => {
        const target = agents?.get?.(targetId);
        if (!target) { if (!resumeGuarded) throw new Error('Cannot verify the helper model.'); return; }
        let current;
        try { current = target.session?.requestHeader?.()?.config ?? target.options; } catch { /* fail closed */ }
        if (!permits(current?.provider, current?.model)) throw new Error('Only a verified local helper can receive messages.');
      };
      const sendGuard = original => function(sender, targetId, ...rest) {
        if (sender?.session?.header?.parentSession !== targetId) checkTarget(sender, targetId);
        return original.call(this, sender, targetId, ...rest);
      };
      const sendGuarded = install(service, 'sendMessage', sendGuard);
      const deliverGuarded = install(service, Symbol.for('dsh.subagent.deliverPrompt'), original => function(parent, targetId, ...rest) {
        checkTarget(parent, targetId);
        return original.call(this, parent, targetId, ...rest);
      });
      messagingGuarded = sendGuarded && deliverGuarded && resumeGuarded;
      if (!resumeGuarded || !sendGuarded || !deliverGuarded) throw new Error('Helper delivery protection is unavailable.');
      const original = service?.startActivation;
      if (typeof original === 'function') {
        const guard = function (spec) {
          const parent = spec?.request?.parent;
          let current;
          try { current = parent?.session?.requestHeader?.()?.config ?? parent?.options; } catch { /* fail closed */ }
          const selected = spec?.request?.agentOptions ?? {};
          const provider = selected.provider ?? current?.provider;
          const model = selected.model ?? current?.model;
          if (!permits(provider, model)) throw new Error('Helpers may use local models only.');
          return original.call(this, spec);
        };
        service.startActivation = guard;
        guarded = Object.getOwnPropertyDescriptor(service, 'startActivation')?.value === guard;
        if (guarded && ctx.effect) ctx.effect(() => () => { if (Object.getOwnPropertyDescriptor(service, 'startActivation')?.value === guard) service.startActivation = original; });
      }
    } catch { /* the workflow tool below fails closed if service interception is unavailable */ }
  }

  const wrapSubagent = def => {
    if (wrapped.has(def)) return;
    wrapped.add(def);
    const original = def.execute;
    def.description = `${def.description}${blocked.size ? ' Use this tool when the person asks to ask a subagent or helper; do not look for the model yourself in files or the environment. Helpers can use local models only; cloud models must be selected for the main chat.' : SUBAGENT_GUIDANCE}`;
    const props = def.parameters?.properties;
    if (props?.model) props.model = { ...props.model, description: blocked.size ? 'The local model to use for the helper: its name or "local". Omit it to inherit a local chat model.' : MODEL_WORDS };
    if (props?.provider) props.provider = { ...props.provider, description: blocked.size ? 'Optional local model provider.' : PROVIDER_WORDS };
    def.execute = function execute(args, exec) {
      const request = args && typeof args === 'object' ? args : {};
      if (blocked.size && !request.provider && !request.model) {
        let current;
        try { current = exec?.agent?.session?.requestHeader?.()?.config?.provider ?? exec?.agent?.options?.provider; } catch { /* fail closed */ }
        if (!current || blocked.has(current)) throw new Error('Choose an allowed model for a helper. This cloud model cannot be inherited by a helper.');
      }
      const problem = modelProblem(routes, request);
      if (problem) throw new Error(problem);
      const settled = subagentArgs(routes, request);
      return original.call(this, settled.args, exec);
    };
  };

  const wrapList = def => {
    if (wrapped.has(def)) return;
    wrapped.add(def);
    def.description = 'List the models a helper agent can be started on, by the names the person knows. Call it with no arguments, then give `model` (a name or id from the list, or "local") to the subagent tool.';
    def.execute = function execute() {
      return routes.length
        ? `Models a helper can use:\n${routeList(routes)}\nStart one with the subagent tool: model = its name or id.`
        : 'No other model is set up. A helper agent uses this chat\'s own model.';
    };
  };

  const wrapAll = () => {
    let agents;
    try { agents = ctx.get('agents')?.list?.() ?? []; } catch { return; }
    for (const agent of agents) {
      try {
        const sub = ctx.tools.get('subagent', agent);
        if (sub) wrapSubagent(sub);
        const fork = ctx.tools.get('subagent_fork', agent);
        if (fork && blocked.size) wrapSubagent(fork);
        const workflow = ctx.tools.get('workflow', agent);
        if (workflow && blocked.size && !guarded && !wrapped.has(workflow)) {
          wrapped.add(workflow);
          workflow.execute = () => { throw new Error('Workflow is unavailable while cloud models are connected.'); };
        }
        const message = ctx.tools.get('send_message', agent);
        if (message && blocked.size && !messagingGuarded && !wrapped.has(message)) {
          wrapped.add(message);
          message.execute = () => { throw new Error('Helper messaging is unavailable while cloud models are connected.'); };
        }
        const list = ctx.tools.get('list_subagent_models', agent);
        if (list) wrapList(list);
      } catch { /* a tool that is not there yet is wrapped at the next change */ }
    }
  };
  ctx.on('tools/change', wrapAll);
  wrapAll();
}
