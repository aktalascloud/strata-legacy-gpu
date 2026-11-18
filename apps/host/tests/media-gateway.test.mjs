import test from 'node:test';
import assert from 'node:assert/strict';
import { generateGatewaySound, mediaGatewayOrigin, readMediaCapabilities } from '../server/media-gateway.mjs';

const local = 'http://10.1.2.3:5003';

test('media detection only reads capabilities from the selected private origin', async () => {
  for (const url of ['http://example.test', 'http://127.0.0.1', 'http://10.1.2.3:5003/?r=x', 'http://x:y@10.1.2.3:5003', `${local}/v1/media/generations`]) assert.throws(() => mediaGatewayOrigin(url));
  const seen = [];
  const result = await readMediaCapabilities(`${local}/media`, async (url, options) => {
    seen.push(url);
    assert.ok(url.startsWith(`${local}/v1/`));
    assert.equal(options.redirect, 'error');
    assert.equal(options.method, undefined);
    assert.equal(options.body, undefined);
    if (url.includes('/media/')) return Response.json({ gui: '/media' });
    if (url.includes('/audio/')) return Response.json({ tts: true, stt: true, sfx: true, sfx_endpoint: '/v1/audio/sfx' });
    return new Response(null, { status: 503 });
  });
  assert.equal(seen.length, 5);
  assert.equal(result.studio, `${local}/media`);
  assert.deepEqual(result.capabilities, { images: null, redraw: null, upscale: null, videos: null, music: null, speech: true, transcription: true, soundEffects: true });
});

test('sound generation requires explicit valid input and accepts only audio', async () => {
  const unexpected = () => { throw new Error('network must not be called'); };
  await assert.rejects(generateGatewaySound(local, { prompt: ' x ', duration: 100 }, { fetcher: unexpected }), /duration/);
  await assert.rejects(generateGatewaySound(local, { prompt: 'wind', duration: 5 }, { fetcher: async () => Response.json({ irrelevant: 1 }) }), /audio/);
  const result = await generateGatewaySound(local, { prompt: 'wind', duration: 5, secret: 'not forwarded' }, { fetcher: async (url, options) => {
    assert.equal(url, `${local}/v1/audio/sfx`);
    assert.equal(options.redirect, 'error');
    assert.deepEqual(JSON.parse(options.body), { prompt: 'wind', duration: 5, response_format: 'wav' });
    return new Response(Buffer.from('audio'), { headers: { 'Content-Type': 'audio/wav' } });
  } });
  assert.equal(result.type, 'audio/wav');
  assert.equal(result.audio.toString(), 'audio');
});
