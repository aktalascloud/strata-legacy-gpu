import type { ModelProviders, RemoteModelSelection } from './types';

export function availableFreeLlmHelpers(providers: ModelProviders | null) {
  const supported = ['nvidia/nemotron-3-ultra-550b-a55b:free', 'dots-studio/dots-3-note-preview:free'];
  const cloud = supported.flatMap(modelId => {
    const connection = providers?.connections.find(c => c.kind === 'provider' && c.provider === 'freellm' && c.baseUrl === 'https://ai-gateway.kilo.ai/api/v1' && c.protocol === 'openai-chat' && !c.apiKeySet && c.models.some(m => m.id === modelId));
    const model = connection?.models.find(m => m.id === modelId);
    return connection && model ? [{ connectionId: connection.id, modelId, name: model.name, route: 'cloud' as const }] : [];
  });
  const lan = (providers?.connections ?? []).filter(c => c.kind === 'provider' && c.provider === 'koboldcpp-lan' && c.protocol === 'openai-chat').flatMap(connection => connection.models.map(model => ({ connectionId: connection.id, modelId: model.id, name: model.name, route: 'lan' as const })));
  return [...cloud, ...lan];
}

export function selectedFreeLlmHelpers(providers: ModelProviders | null, choices: RemoteModelSelection[] | undefined): RemoteModelSelection[] {
  if (!Array.isArray(choices)) return [];
  return availableFreeLlmHelpers(providers).filter(helper => choices.some(choice => choice?.connectionId === helper.connectionId && choice?.modelId === helper.modelId)).slice(0, 4)
    .map(({ connectionId, modelId }) => ({ connectionId, modelId }));
}

export function canSendToFreeLlm(message: string, { direct, hasQuotes = false, hasImages = false }: { direct: boolean; hasQuotes?: boolean; hasImages?: boolean }): boolean {
  const text = message.trim();
  return direct && !!text && !text.startsWith('/') && !hasQuotes && !hasImages && !/^Attached [^\r\n]+$/m.test(text);
}
