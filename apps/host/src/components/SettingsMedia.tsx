import { useEffect, useRef, useState } from 'react';
import { api } from '../lib/client';
import { tr } from '../lib/i18n';
import { openExternal } from '../lib/open-external';
import { Btn, ErrorNotice, Pill } from './ui';

const operations = {
    images: 'Generate images', redraw: 'Redraw images', upscale: 'Upscale images', videos: 'Generate video',
    music: 'Generate music', speech: 'Text to speech', transcription: 'Transcribe audio', soundEffects: 'Sound effects',
};
type Probe = { url: string; studio: string; capabilities: Record<keyof typeof operations, boolean | null> };

export function SettingsMedia() {
    const [url, setUrl] = useState(''), [saved, setSaved] = useState(''), [probe, setProbe] = useState<Probe | null>(null);
    const [pending, setPending] = useState<'load' | 'test' | 'save' | 'sound' | null>('load');
    const [error, setError] = useState(''), [notice, setNotice] = useState('');
    const [prompt, setPrompt] = useState(''), [seconds, setSeconds] = useState('5'), [audio, setAudio] = useState('');
    const sound = useRef<AbortController | null>(null);

    useEffect(() => {
        const controller = new AbortController();
        void api.get<{ url: string }>('/api/media-gateway', controller.signal).then(value => {
            setUrl(value.url); setSaved(value.url);
        }).catch(e => { if (!controller.signal.aborted) setError(e.message); })
            .finally(() => { if (!controller.signal.aborted) setPending(null); });
        return () => { controller.abort(); sound.current?.abort(); };
    }, []);
    useEffect(() => () => { if (audio) URL.revokeObjectURL(audio); }, [audio]);

    async function changeConnection(method: 'test' | 'save') {
        setPending(method); setError(''); setNotice('');
        try {
            if (method === 'test') {
                const result = await api.post<Probe>('/api/media-gateway/test', { url });
                setProbe(result); setUrl(result.url);
            } else {
                const result = await api.put<{ url: string }>('/api/media-gateway', { url: url.trim() });
                setSaved(result.url); setUrl(result.url); setNotice('Saved.');
            }
        } catch (e) {
            if (method === 'test') setProbe(null);
            setError(e instanceof Error ? e.message : String(e));
        } finally { setPending(null); }
    }

    async function generateSound() {
        const controller = new AbortController();
        sound.current = controller;
        setPending('sound'); setError(''); setNotice(''); setAudio('');
        try {
            const res = await fetch('/api/media-gateway/sound', { method: 'POST', signal: controller.signal, headers: { 'content-type': 'application/json' }, body: JSON.stringify({ prompt, duration: Number(seconds) }) });
            if (!res.ok) throw new Error((await res.json()).error ?? 'The media gateway did not return audio.');
            const blob = await res.blob();
            controller.signal.throwIfAborted();
            setAudio(URL.createObjectURL(blob));
        } catch (e) {
            if (!controller.signal.aborted) setError(e instanceof Error ? e.message : String(e));
        } finally {
            if (sound.current === controller) { sound.current = null; setPending(null); }
        }
    }

    return <div className="stack stack--lg settings-body">
      <section className="settings-section stack">
        <h2 className="h3">{tr('Media')}</h2>
        <p className="small muted">{tr('Connect to a media gateway on your private network. Testing the connection checks capabilities without starting a generation.')}</p>
        <label className="input-field"><span>{tr('Media gateway address')}</span><input className="st-input" type="url" placeholder="http://192.168.1.20:5003" value={url} disabled={!!pending} onChange={e => { setUrl(e.target.value); setProbe(null); setError(''); setNotice(''); }}/></label>
        <div className="media-gateway-actions">
          <Btn size="sm" icon="refresh" disabled={!!pending || !url.trim()} onClick={() => void changeConnection('test')}>{tr(pending === 'test' ? 'Checking…' : 'Test connection')}</Btn>
          <Btn size="sm" variant="primary" disabled={!!pending || url.trim() === saved} onClick={() => void changeConnection('save')}>{tr(pending === 'save' ? 'Saving…' : 'Save settings')}</Btn>
          {probe ? <Btn size="sm" icon="link" onClick={() => void openExternal(probe.studio)}>{tr('Open media studio')}</Btn> : null}
        </div>
        {notice ? <p className="small muted" role="status">{tr(notice)}</p> : null}
        {probe ? <div className="media-gateway-actions">{Object.entries(operations).map(([key, label]) => {
            const available = probe.capabilities[key as keyof typeof operations];
            return <Pill key={key} tone={available ? 'accent' : 'plain'}>{tr(label)} · {tr(available === null ? 'Unknown' : available ? 'Available' : 'Unavailable')}</Pill>;
        })}</div> : null}
        {error ? <ErrorNotice message={error}/> : null}
      </section>
      {probe?.capabilities.soundEffects && probe.url === saved ? <section className="st-card stack">
        <h3 className="h4">{tr('Sound effects')}</h3>
        <label className="input-field"><span>{tr('Sound description')}</span><textarea className="st-input" value={prompt} maxLength={2000} disabled={!!pending} onChange={e => setPrompt(e.target.value)}/></label>
        <label className="input-field"><span>{tr('Duration in seconds')}</span><input className="st-input" type="number" min="0.25" max="60" step="0.25" value={seconds} disabled={!!pending} onChange={e => setSeconds(e.target.value)}/></label>
        <div className="media-gateway-actions"><Btn size="sm" variant="primary" disabled={!!pending || !prompt.trim() || !(Number(seconds) >= 0.25 && Number(seconds) <= 60)} onClick={() => void generateSound()}>{tr(pending === 'sound' ? 'Generating…' : 'Generate sound')}</Btn>
            {pending === 'sound' ? <Btn size="sm" onClick={() => sound.current?.abort()}>{tr('Stop')}</Btn> : null}</div>
        {audio ? <audio controls src={audio}/> : null}
      </section> : null}
    </div>;
}
