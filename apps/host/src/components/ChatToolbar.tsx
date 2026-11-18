import {sessionTitle} from '../lib/session-title';
import { tr } from '../lib/i18n';
import { useEffect, useRef, useState } from 'react';
import { ArtifactTabs, type ExtraPreviewTab } from './ArtifactPanel';
import { FloatingMenu } from './FloatingMenu';
import { Popover } from './Popover';
import { Btn, Dialog, Icon, IconBtn } from './ui';
import { SamplingDrawer } from '../app/SamplingDrawer';
import { downloadSessionLog } from '../lib/session-log';
import { SubagentRow } from './SubagentRow';
import { ChatModelPicker } from './ChatModelPicker';
import { runningAgents } from '../lib/agents';
import { setChatPreferences, useStore } from '../lib/store';
import { useNative } from '../lib/native';
import { availableFreeLlmHelpers, selectedFreeLlmHelpers } from '../lib/free-llm-helpers';
import type { RemoteModelSelection, Session } from '../lib/types';
import type { PreviewArtifact } from '../lib/artifacts';
export function ChatToolbar({ session, items, selected, onSelect, onClose, onCloseTab, inline, expanded, onExpand, extraTabs = [], previewWidth }: {
    previewWidth?: number;
    extraTabs?: ExtraPreviewTab[];
    session: Session | null;
    items: PreviewArtifact[];
    selected: string | null;
    onSelect: (id: string) => void;
    onClose: () => void;
    onCloseTab: (id: string) => void;
    inline: boolean;
    expanded: boolean;
    onExpand: () => void;
}) {
    const remote = useStore(s => s.remoteModel);
    const providers = useStore(s => s.providers), streaming = useStore(s => s.streaming);
    const connected = useStore(s => s.connection === 'live');
    const native = useNative();
    const swift = native?.instances.some(i => i.id === native.defaultId && i.model === 'swift-1.5-iq3-s' && i.status === 'ready');
    const helpers = availableFreeLlmHelpers(providers);
    const canUseHelpers = connected && !!swift && !remote && session?.preferences?.agent !== false && helpers.length > 0;
    const chosenHelpers = selectedFreeLlmHelpers(providers, session?.preferences?.freeLlmHelpers);
    const [helperDraft, setHelperDraft] = useState<RemoteModelSelection[] | null>(null);
    const [agents, setAgents] = useState(false), [menu, setMenu] = useState(false), [settings, setSettings] = useState(false);
    const agentsRef = useRef<HTMLButtonElement>(null), menuRef = useRef<HTMLButtonElement>(null);
    const count = runningAgents(session?.agents ?? []);
    const [now, setNow] = useState(Date.now);
    useEffect(() => { if (!agents || !count)
        return; setNow(Date.now()); const timer = setInterval(() => setNow(Date.now()), 1000); return () => clearInterval(timer); }, [agents, count, session?.id]);
    useEffect(() => setAgents(false), [session?.id]);
    useEffect(() => setHelperDraft(null), [session?.id]);
    const previews = !!selected && inline;
    const title = session ? sessionTitle(session) : tr('New chat');
    return <header className="chat-toolbar" style={previews && !expanded && previewWidth ? { gridTemplateColumns: `minmax(0,1fr) ${previewWidth}px` } : undefined} data-timeskip={selected?.startsWith('time-skip:') || undefined} data-preview={previews || undefined} data-expanded={expanded && previews || undefined}>
    <div className="chat-toolbar__conversation"><h1 title={title}>{title}</h1><ChatModelPicker /><button ref={agentsRef} className="chat-agents" title={tr(count ? `${count} subagents running · View overview` : 'View subagent overview')} aria-label={tr(count ? `${count} subagents running — show overview` : 'Subagents — show overview')} aria-haspopup="dialog" aria-expanded={agents} data-working={count > 0 || undefined} onClick={() => setAgents(v => !v)}><Icon name="experts" size={17}/>{tr(count > 0 ? <span className="agent-live-dot"/> : null)}<span className="chat-agents__label">{tr("Subagents")}</span>{canUseHelpers && chosenHelpers.length ? <span className="chat-agents__count" title={tr("{0} helpers enabled", [chosenHelpers.length])}>{tr('Helpers')} {chosenHelpers.length}</span> : null}{tr(session?.agents?.length ? <span className="chat-agents__count">{tr(count || session.agents.length)}</span> : null)}<Icon name="chevron" className={agents ? 'is-open' : ''} size={13}/></button><span className="spacer"/><button ref={menuRef} className="st-btn st-btn--icon" title={tr("Chat options")} aria-label={tr("Chat options")} aria-haspopup="menu" aria-expanded={menu} onClick={() => setMenu(v => !v)}><Icon name="ellipsis"/></button>{tr(!selected && (items.length || extraTabs.length) ? <IconBtn name="panel" title={tr("Open previews")} onClick={() => onSelect(extraTabs.at(-1)?.id ?? items[0].id)}/> : null)}</div>
    {tr(previews ? <div className="chat-toolbar__previews"><ArtifactTabs extraTabs={extraTabs} onCloseTab={onCloseTab} items={items} selected={selected} onSelect={onSelect}/><div className="preview-window-actions"><div id="preview-file-actions" className="preview-file-actions"/><IconBtn name={expanded ? 'contract' : 'expand'} title={tr(expanded ? 'Exit full screen preview' : 'Full screen preview')} onClick={onExpand}/><IconBtn name="panel" title={tr("Collapse preview sidebar")} onClick={onClose}/></div></div> : null)}
    {tr(agents ? <Popover anchor={agentsRef.current} title={tr(session?.agents?.length ? "Subagents" : "No subagents recorded")} detail={session?.agents?.length ? <>{tr(count)}{tr(" running \u00B7 ")}{tr(session.agents.filter(a => a.status === 'completed').length)}{tr(" completed \u00B7 ")}{tr(session.agents.length)}{tr(" total")}</> : undefined} width={460} onClose={() => setAgents(false)}>
      {canUseHelpers ? <div className="cloud-helper-row"><Btn size="sm" icon="experts" disabled={streaming} onClick={() => { setAgents(false); setHelperDraft(chosenHelpers); }}>{tr('Parallel helpers')}</Btn>{chosenHelpers.length ? <span className="small muted">{tr('{0} helpers enabled', [chosenHelpers.length])}</span> : null}</div> : null}
      {session?.agents?.map(a => <SubagentRow key={a.id} agent={a} now={now} sessionId={session && !session.showcase ? session.id : undefined}/>)}
    </Popover> : null)}
    {tr(menu ? <FloatingMenu anchor={menuRef.current} title={tr("Chat options")} onClose={() => setMenu(false)}><button role="menuitem" className="menu__item" disabled={!!remote} title={tr(remote ? "API models use their provider’s response settings." : undefined)} onClick={() => { setMenu(false); setSettings(true); }}><Icon name="sliders"/>{tr("Response settings")}</button><button role="menuitem" className="menu__item" disabled={!session} onClick={() => { if (session)
        downloadSessionLog(session); setMenu(false); }}><Icon name="download"/>{tr("Download session log")}</button></FloatingMenu> : null)}
    <SamplingDrawer open={settings} onClose={() => setSettings(false)}/>
    <Dialog open={helperDraft !== null && canUseHelpers} compact title={tr('Parallel helpers')} onClose={() => setHelperDraft(null)} actions={<>
      <Btn onClick={() => setHelperDraft(null)}>{tr('Cancel')}</Btn>
      <Btn variant="primary" disabled={streaming || !canUseHelpers} onClick={() => { setChatPreferences(session?.id, { freeLlmHelpers: selectedFreeLlmHelpers(providers, helperDraft ?? []) }); setHelperDraft(null); }}>{tr('Save settings')}</Btn>
    </>}>
      <p>{tr('Swift drafts short text subtasks from your current message. The selected models receive those subtasks in parallel, then Swift combines their answers.')}</p>
      <p className="small muted">{tr('Helpers receive only the subtasks. Chat history and attachments stay on this computer.')}</p>
      <p className="small muted">{tr('Helpers work on text without tools. Commands and messages with attachments use the normal chat.')}</p>
      {helpers.some(h => h.route === 'cloud') ? <p className="small muted">{tr('FreeLLM sends your messages to Kilo and its providers. They may use prompts and answers to improve models. Do not send confidential data. NVIDIA free models are for trial use.')}</p> : null}
      {helpers.some(h => h.route === 'lan') ? <p className="small muted">{tr('KoboldCpp helpers receive subtasks at the private network address you saved in Models.')}</p> : null}
      <div className="stack stack--sm">{helpers.map(({ name, connectionId, modelId, route }) => {
        const checked = helperDraft?.some(h => h.connectionId === connectionId && h.modelId === modelId) ?? false;
        return <label className="run-default-choice" key={`${connectionId}:${modelId}`}>
        <input type="checkbox" checked={checked} disabled={!checked && (helperDraft?.length ?? 0) >= 4} onChange={e => {
          const checked = e.currentTarget.checked;
          setHelperDraft(current => checked ? [...(current ?? []), { connectionId, modelId }] : (current ?? []).filter(h => h.connectionId !== connectionId || h.modelId !== modelId));
        }}/><span>{name}<small>{route === 'cloud' ? 'FreeLLM · Kilo' : 'KoboldCpp · LAN'}</small></span>
      </label>; })}</div>
    </Dialog>
  </header>;
}
