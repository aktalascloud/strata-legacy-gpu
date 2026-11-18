import { useEffect, useState } from 'react';
import { api } from '../lib/client';
import { tr } from '../lib/i18n';
import { Btn } from './ui';

type Policy = { thresholdTokens: number; keepMessages: number };

export function CompactionSettings() {
  const [policy, setPolicy] = useState<Policy | null>(null);
  const [pending, setPending] = useState(false);
  const [notice, setNotice] = useState('');
  useEffect(() => {
    let live = true;
    api.get<Policy>('/api/agent/compaction').then(value => { if (live) setPolicy(value); })
      .catch(() => { if (live) setNotice('Could not load compaction settings.'); });
    return () => { live = false; };
  }, []);
  async function save() {
    if (!policy) return;
    setPending(true); setNotice('');
    try { setPolicy(await api.post<Policy>('/api/agent/compaction', policy)); setNotice('Saved.'); }
    catch { setNotice('Could not save compaction settings.'); }
    finally { setPending(false); }
  }
  if (!policy) return <span>{tr(notice || 'Loading…')}</span>;
  return <div className="stack stack--sm">
    <label>{tr('Compaction threshold (tokens; 0 = automatic)')}
      <input className="st-input" type="number" min={0} max={10000000} step={1} value={policy.thresholdTokens}
        onChange={e => setPolicy({ ...policy, thresholdTokens: Number(e.target.value) })}/></label>
    <label>{tr('Recent messages to keep (0 = automatic)')}
      <input className="st-input" type="number" min={0} max={1000} step={1} value={policy.keepMessages}
        onChange={e => setPolicy({ ...policy, keepMessages: Number(e.target.value) })}/></label>
    <small>{tr('The threshold is limited by the model window and space for the reply. Changes apply to the next agent turn.')}</small>
    <small>{tr('These settings apply to agent chats. Plain chat and /compact use their existing behavior.')}</small>
    <div className="row"><Btn size="sm" disabled={pending} onClick={() => void save()}>{tr('Save')}</Btn>{notice ? <span role="status">{tr(notice)}</span> : null}</div>
  </div>;
}
