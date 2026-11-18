import { isIPv4 } from 'node:net';

export function privateLanUrl(value) {
  try {
    const url = new URL(value);
    if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password || url.search || url.hash ||
        !isIPv4(url.hostname)) return null;
    const [a, b] = url.hostname.split('.').map(Number);
    if (a !== 10 && !(a === 172 && b >= 16 && b < 32) && !(a === 192 && b === 168)) return null;
    return url;
  } catch {
    return null;
  }
}

export function isLanKobold(connection) {
  const url = connection?.provider === 'koboldcpp-lan' && privateLanUrl(connection.baseUrl);
  return !!url && url.pathname.replace(/\/+$/, '') === '/v1' && connection.protocol === 'openai-chat';
}
