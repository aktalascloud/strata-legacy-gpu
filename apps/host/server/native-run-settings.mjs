import { merge } from './native-user-args.mjs';

export const catalogIdForLocal = (model, profile) => profile?.model === model && model === 'swift-1.5-iq3-s' ? 'swift-iq3_s' : undefined;

/** Non-secret settings from the configuration handed to the running server. */
export function nativeRunSettings(config) {
  const args = merge(config.args ?? [], config.user_args ?? []);
  const value = flag => { const at = args.lastIndexOf(flag); return at >= 0 ? args[at + 1] : undefined; };
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
