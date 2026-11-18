import { privateLanUrl } from './lan-kobold.mjs';

export function mediaGatewayOrigin(value) {
  const url = typeof value === 'string' && value.length < 256 && privateLanUrl(value.trim());
  if (!url || !['/', '/media', '/media/'].includes(url.pathname)) throw new Error('Enter the media gateway address on your private network.');
  return url.origin;
}

async function boundedBytes(response, limit) {
  if (!response.ok || !response.body || Number(response.headers.get('content-length')) > limit) {
    await response.body?.cancel();
    throw new Error('The media gateway did not return a usable response.');
  }
  const reader = response.body.getReader();
  let bytes = 0;
  const chunks = [];
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) return Buffer.concat(chunks, bytes);
      bytes += value.length;
      if (bytes > limit) throw new Error('The media gateway response is too large.');
      chunks.push(value);
    }
  } finally {
    await reader.cancel().catch(() => undefined);
  }
}

export async function readMediaCapabilities(value, fetcher = fetch) {
  const url = mediaGatewayOrigin(value);
  const read = async kind => {
    try {
      const response = await fetcher(`${url}/v1/${kind}/capabilities`, { redirect: 'error', signal: AbortSignal.timeout(3000) });
      return JSON.parse(await boundedBytes(response, 64 * 1024));
    } catch { return null; }
  };
  const [media, audio, music, image, video] = await Promise.all(['media', 'audio', 'music', 'images', 'videos'].map(read));
  if (!media || media.gui !== '/media') throw new Error('No compatible media gateway answered at this address.');
  return {
    url, studio: `${url}/media`,
    capabilities: {
      images: image ? image.operations?.txt2img?.supported === true : null,
      redraw: image ? image.operations?.img2img?.supported === true : null,
      upscale: image ? image.operations?.upscale?.supported === true : null,
      videos: video ? video.enabled === true : null,
      music: music ? music.generate_endpoint === '/api/extra/music/generate' : null,
      speech: audio ? audio.tts === true : null,
      transcription: audio ? audio.stt === true : null,
      soundEffects: audio ? audio.sfx === true && audio.sfx_endpoint === '/v1/audio/sfx' : null,
    },
  };
}

export async function generateGatewaySound(value, body, { fetcher = fetch, signal } = {}) {
  const url = mediaGatewayOrigin(value);
  const prompt = typeof body?.prompt === 'string' ? body.prompt.trim() : '';
  const duration = body?.duration;
  if (!prompt || prompt.length > 2000 || !Number.isFinite(duration) || duration < 0.25 || duration > 60) throw new Error('Enter a sound prompt and a duration from 0.25 to 60 seconds.');
  const timeout = AbortSignal.timeout(300000);
  const response = await fetcher(`${url}/v1/audio/sfx`, {
    method: 'POST', headers: { 'content-type': 'application/json' }, redirect: 'error',
    signal: signal ? AbortSignal.any([signal, timeout]) : timeout,
    body: JSON.stringify({ prompt, duration, response_format: 'wav' }),
  });
  const type = response.headers.get('content-type')?.split(';')[0];
  if (!['audio/wav', 'audio/mpeg'].includes(type)) {
    await response.body?.cancel();
    throw new Error('The media gateway did not return audio.');
  }
  const audio = await boundedBytes(response, 16 * 1024 * 1024);
  if (!audio.length) throw new Error('The media gateway did not return audio.');
  return { type, audio };
}
