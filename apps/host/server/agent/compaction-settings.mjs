/** User policy: 0 tokens means an automatic, window-aware threshold. */
export function compactionSettings(value = {}) {
  const thresholdTokens = value.thresholdTokens ?? 0;
  const keepMessages = value.keepMessages ?? 0;
  if (!Number.isSafeInteger(thresholdTokens) || thresholdTokens < 0 || thresholdTokens > 10_000_000)
    throw new Error('The compaction threshold must be a whole number from 0 to 10000000 tokens.');
  if (!Number.isSafeInteger(keepMessages) || keepMessages < 0 || keepMessages > 1000)
    throw new Error('The number of recent messages must be a whole number from 0 to 1000.');
  return { thresholdTokens, keepMessages };
}

export function compactPolicy(provider, model, context, output, headroom, options) {
  const { thresholdTokens, keepMessages } = compactionSettings(options);
  const w = Number.isFinite(context) && context > 0 ? context : 32768;
  const policy = { provider, model, headroomTokens: headroom };
  if (thresholdTokens) {
    // Harness additionally clamps to window minus output and headroom.
    policy.thresholdRatio = Math.min(1, thresholdTokens / w);
    if (!keepMessages) policy.retainRatio = Math.min(0.16, policy.thresholdRatio / 2);
  }
  // The backend applies exact message retention after the Harness selects a balanced range.
  if (keepMessages) policy.retainTokens = 0;
  return policy;
}

/** Restrict a Harness-selected range without splitting an assistant tool-call/result pair. */
export function protectedCompactionRange(session, start, end, keepMessages, balancedBefore) {
  if (!keepMessages) return { start, end };
  const nodes = session.surface.nodes;
  const begin = nodes.indexOf(start), originalEnd = nodes.indexOf(end);
  if (begin < 0 || originalEnd < begin) throw new Error('The compaction range no longer matches the session.');
  let remaining = keepMessages, boundary = nodes.length;
  for (let i = nodes.length - 1; i >= 0 && remaining > 0; i--) {
    const event = session.eventAt(nodes[i]);
    const content = event?.data?.message?.content;
    const visibleAssistant = event?.type === 'assistant/message' && (typeof content === 'string' ||
      Array.isArray(content) && content.some(block => (block.type === 'text' || block.type === 'reasoning') && block.text));
    // Harness user/message data is the message itself. Runtime snapshots and compact checkpoints
    // use the same event type but are not visible user turns and must not spend the retention count.
    const userKind = event?.type === 'user/message' ? event.data?.source?.kind : null;
    if (event?.type === 'user/message' && typeof userKind !== 'string')
      throw new Error('A conversation message has no valid source; refusing to compact it.');
    if (userKind === 'user' || visibleAssistant) { boundary = i; remaining--; }
  }
  // Preserve any earlier event needed to keep tool results paired with their calls.
  while (boundary > begin && boundary < nodes.length && !balancedBefore(session, nodes[boundary])) boundary--;
  const last = Math.min(originalEnd, boundary - 1);
  if (last < begin) throw Object.assign(new Error('The protected recent messages leave no safe history to compact.'), { code: 'CONTEXT_WINDOW_EXCEEDED' });
  return { start, end: nodes[last] };
}
