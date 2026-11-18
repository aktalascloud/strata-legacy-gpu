/** Keep recent visible messages while preserving the Harness overflow retry and durable transactions. */
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import { protectedCompactionRange } from '../compaction-settings.mjs';

// The plugin is outside the Harness tree; resolve its pinned runtime from the actual Harness entrypoint.
const require = createRequire(process.argv[1]);
const { BasicCompactionEngine } = await import(pathToFileURL(require.resolve('@deepseek-ai/dsh-compaction-basic')).href);
const { toolPairingBalancedBefore } = await import(pathToFileURL(require.resolve('@deepseek-ai/dsh-compaction')).href);
const keep = Number(process.env.STRATA_COMPACTION_KEEP_MESSAGES ?? 0);
if (!Number.isSafeInteger(keep) || keep < 1 || keep > 1000) throw new Error('Invalid recent-message retention setting.');

export default class StrataCompaction extends BasicCompactionEngine {
  async compactRegion(start, end, agent, signal) {
    const range = protectedCompactionRange(agent.session, start, end, keep, toolPairingBalancedBefore);
    return super.compactRegion(range.start, range.end, agent, signal);
  }
}
