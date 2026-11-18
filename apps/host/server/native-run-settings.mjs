import { capture, flagOf, groups, merge, setFlag } from './native-user-args.mjs';

export const catalogIdForLocal = (model, profile) => profile?.model === model && model === 'swift-1.5-iq3-s' ? 'swift-iq3_s' : undefined;

export const LOCAL_RUN_FIELDS = [
  { id: 'context_tokens', flag: '--max-context', label: 'Conversation context', group: 'GPU & memory', type: 'number', min: 1024, max: 262144 },
  { id: 'kv_format', flag: '--kv', label: 'Context memory', group: 'GPU & memory', type: 'enum', choices: ['q4_0', 'int8', 'k8v4'] },
  { id: 'prefill_chunk', flag: '--prefill', label: 'Prefill chunk size', group: 'GPU & memory', type: 'string' },
  { id: 'pool_workers', flag: '--pool-workers', label: 'CPU workers', group: 'GPU & memory', type: 'number', min: 0, max: 256 },
  { id: 'vision_device', label: 'Image encoder device', group: 'Image reading', type: 'enum', choices: ['cpu', 'gpu', 'yes', 'no'] },
  { id: 'vision_threads', label: 'Image encoder threads', group: 'Image reading', type: 'number', min: 1, max: 256 },
];

export const effectiveArgs = config => merge(config.args ?? [], capture(config));
const lastFlag = (args, flag) => groups(args).findLast(group => flagOf(group) === flag)?.[1];
const wholeNumber = value => value != null && /^\d+$/.test(String(value)) ? Number(value) : null;

export function localRunFields(config) {
  const args = effectiveArgs(config);
  return Object.fromEntries(LOCAL_RUN_FIELDS.map(({ id, flag, type }) => {
    const value = flag ? lastFlag(args, flag) : id === 'vision_threads' ? config.vision?.threads
      : config.ui_vision_enabled === false ? 'no' : config.ui_vision_device ?? (config.vision?.gpu === false ? 'cpu' : config.vision?.gpu === true ? 'gpu' : 'yes');
    return [id, type === 'number' ? wholeNumber(value) : value ?? null];
  }));
}

export function savedReserve(config) {
  return wholeNumber(lastFlag(capture(config), '--vram-reserve-mib') ?? config.vram_reserve_mib ?? lastFlag(config.args, '--vram-reserve-mib'));
}

/** Synchronize an edit made in the raw arguments editor with the saved overrides. */
export function setLocalArgs(config, original, patch) {
  const before = effectiveArgs(original);
  if (patch.args) {
    config.args = patch.args;
    config.user_args = capture({ args: patch.args, args_written: before, user_args: capture(original) }, new Set());
    if (lastFlag(before, '--vram-reserve-mib') !== lastFlag(patch.args, '--vram-reserve-mib') && !('vram_reserve_mib' in patch)) {
      delete config.vram_reserve_mib;
      delete config.ui_reserve_applied;
    }
  } else {
    config.user_args = capture(original);
  }
  for (const { id, flag } of LOCAL_RUN_FIELDS) {
    if (!(id in patch)) continue;
    if (flag) {
      config.args = setFlag(config.args, flag, patch[id]);
      config.user_args = setFlag(config.user_args, flag, patch[id]);
    } else if (id === 'vision_device') {
      const mode = patch[id];
      if (mode && mode !== 'no' && !config.vision) throw new Error('Prepare this model’s vision files before enabling picture reading.');
      if (mode && mode !== 'no') config.ui_vision_device = mode;
      else delete config.ui_vision_device;
      if (mode) config.ui_vision_enabled = mode !== 'no';
      else delete config.ui_vision_enabled;
      config.ui_vision_chosen = mode !== null;
    } else if (config.vision) {
      config.vision = { ...config.vision };
      if (patch[id] === null) delete config.vision.threads;
      else config.vision.threads = patch[id];
    } else if (patch[id] !== null) {
      throw new Error('Prepare this model’s vision files before enabling picture reading.');
    }
  }
  if (Array.isArray(config.args_written)) config.args_written = [...config.args];
}

/** Non-secret settings from the configuration handed to the running server. */
export function nativeRunSettings(config) {
  const args = effectiveArgs(config);
  const value = flag => lastFlag(args, flag);
  const context = Number(value('--max-context'));
  const kv = value('--kv');
  const vision = config.vision && typeof config.vision === 'object' ? config.vision : null;
  const threads = Number(vision?.threads);
  return {
    context: Number.isInteger(context) && context > 0 ? context : null,
    kv: typeof kv === 'string' && !kv.startsWith('--') ? kv : null,
    vision: !vision ? 'off' : vision.gpu === false ? 'cpu' : vision.gpu === true ? 'gpu' : 'automatic',
    visionThreads: Number.isInteger(threads) && threads > 0 ? threads : null,
  };
}
