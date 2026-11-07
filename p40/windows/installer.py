"""Install this public, weights-free distribution. No credentials, global environment edits or server start."""
from __future__ import annotations
import argparse, re, stat, contextlib, datetime, hashlib, json, os, pathlib, shutil, subprocess, sys, time
import http.client, importlib.util, urllib.error, urllib.request, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]

def sha(path):
    h = hashlib.sha256()
    with pathlib.Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8 << 20), b''): h.update(block)
    return h.hexdigest()

def atomic(path, value):
    path = pathlib.Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    with tmp.open('w', encoding='utf8') as f:
        json.dump(value, f, indent=2); f.write('\n'); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)


def atomic_create(path, value):
    """Complete JSON first; atomically create the name without replacing any existing file."""
    path = pathlib.Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + '.new-', dir=path.parent)
    temporary = pathlib.Path(temporary)
    try:
        with os.fdopen(fd, 'w', encoding='utf8') as f:
            json.dump(value, f, indent=2); f.write('\n'); f.flush(); os.fsync(f.fileno())
        if os.name == 'nt':
            os.rename(temporary, path)  # Windows rename fails if the destination exists.
        else:
            os.link(temporary, path)    # POSIX rename would overwrite; a hard link does not.
    finally:
        temporary.unlink(missing_ok=True)


def commit_initial_profile(root, config, active):
    """Called under install_lock. Never overwrite either user's profile or runtime state."""
    target = root/'strata.json'; state = root/'runtime/active.json'
    if target.exists() or target.is_symlink() or state.exists() or state.is_symlink():
        raise RuntimeError('Existing configuration/runtime state retained; inspect it or use another folder.')
    try:
        atomic_create(target, config)
        atomic_create(state, active)
    except FileExistsError as error:
        # A late creator wins. Do not attempt a racy rollback/unlink of either destination.
        raise RuntimeError('Configuration/runtime state appeared during setup; existing files were preserved. '
                           'Inspect both files before START.cmd; setup did not finish.') from error

@contextlib.contextmanager
def install_lock(root):
    import msvcrt
    path = root / 'install.lock'
    with path.open('a+b') as f:
        f.seek(0)
        if not f.read(1): f.write(b'0'); f.flush()
        f.seek(0)
        try: msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError: raise RuntimeError('Another installer is active. Partial files are preserved.')
        try: yield
        finally: f.seek(0); msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)

def fetch(entry, target, *, url=None, attempts=8):
    """Never append a 200 response to a partial file; never accept wrong size/hash."""
    target = pathlib.Path(target); target.parent.mkdir(parents=True, exist_ok=True)
    part = target.with_name(target.name + '.part')
    provenance = part.with_name(part.name + '.json')
    receipt = target.with_name(target.name + '.verified.json')
    identity = {k: entry[k] for k in ('repo', 'revision', 'remote', 'size', 'sha256')}
    if target.exists():
        st = target.stat()
        old = json.loads(receipt.read_text()) if receipt.exists() else {}
        if old.get('identity') == identity and old.get('mtime_ns') == st.st_mtime_ns and st.st_size == entry['size']:
            print('Verified receipt:', target.name, flush=True); return target
        if st.st_size != entry['size'] or sha(target) != entry['sha256']:
            raise RuntimeError('Existing final file does not match; preserved: ' + target.name)
    else:
        if part.exists() and (not provenance.exists() or json.loads(provenance.read_text()) != identity):
            raise RuntimeError('Partial provenance mismatch; preserved: ' + part.name)
        atomic(provenance, identity)
        from urllib.parse import quote
        address = url or ('https://huggingface.co/' + entry['repo'] + '/resolve/' + entry['revision'] + '/' + quote(entry['remote'], safe='/') + '?download=true')
        for attempt in range(attempts):
            offset = part.stat().st_size if part.exists() else 0
            if offset > entry['size']: raise RuntimeError('Oversized partial file; preserved')
            if offset == entry['size']: break
            headers = {'User-Agent': 'Strata-AVX1-P40-public-installer/1'}
            if offset: headers['Range'] = f'bytes={offset}-'
            try:
                request = urllib.request.Request(address, headers=headers)
                with urllib.request.urlopen(request, timeout=90) as response:
                    status = response.status
                    if offset and status != 206: raise RuntimeError('Server ignored Range; partial preserved, never appended')
                    if status == 206:
                        content_range = response.headers.get('Content-Range', '')
                        import re
                        match = re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)', content_range)
                        if not match or int(match[1]) != offset or int(match[3]) != entry['size']:
                            raise RuntimeError('Wrong Content-Range; partial preserved')
                    elif status != 200: raise RuntimeError('Unexpected HTTP status')
                    print(f'{target.name}: resume {offset:,}/{entry["size"]:,} bytes', flush=True)
                    with part.open('ab') as f:
                        sync_at = f.tell(); progress_at = sync_at
                        while True:
                            block = response.read(4 << 20)
                            if not block: break
                            if f.tell() + len(block) > entry['size']: raise RuntimeError('Response exceeds pinned size')
                            f.write(block)
                            if f.tell() - sync_at >= 32 << 20: f.flush(); os.fsync(f.fileno()); sync_at = f.tell()
                            if f.tell() - progress_at >= 256 << 20:
                                print(f'  {f.tell():,}/{entry["size"]:,}', flush=True); progress_at = f.tell()
                        f.flush(); os.fsync(f.fileno())
            except (urllib.error.URLError, OSError, TimeoutError, http.client.HTTPException) as error:
                if attempt + 1 == attempts: raise RuntimeError('Download paused; rerun INSTALL.cmd to resume') from error
                print('Connection interrupted; partial preserved, retrying.', flush=True)
                time.sleep(min(2 ** attempt, 30))
        if not part.exists() or part.stat().st_size != entry['size']: raise RuntimeError('Incomplete download; partial preserved')
        print('SHA-256:', target.name, flush=True)
        if sha(part) != entry['sha256']: raise RuntimeError('SHA-256 mismatch; partial preserved for inspection')
        os.replace(part, target)
    atomic(receipt, {'identity': identity, 'mtime_ns': target.stat().st_mtime_ns,
                     'verified_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()})
    return target

def check_bundle(root=ROOT):
    manifest = json.loads((root / 'bundle-manifest.json').read_text(encoding='utf8'))
    for row in manifest['files']:
        p = (root / row['path']).resolve()
        if not p.is_relative_to(root.resolve()) or p.is_symlink(): raise RuntimeError('Unsafe bundle path')
        if not p.is_file() or p.stat().st_size != row['bytes'] or sha(p) != row['sha256']:
            raise RuntimeError('Bundle hash mismatch: ' + row['path'])
    print(f'Bundle verified: {len(manifest["files"])} files; no model downloaded or server started.')
    return manifest

def native_preset(root, manifest):
    preset = manifest.get('native_preset')
    if (not isinstance(preset, dict) or not isinstance(preset.get('model_id'), str) or not preset['model_id'] or
            not isinstance(preset.get('model_name'), str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._/-]{0,255}', preset['model_name']) or
            not isinstance(preset.get('display_name'), str) or not preset['display_name'] or
            type(preset.get('reason_modes')) is not bool or preset.get('reason_mode') not in ('off', 'auto', 'ultra') or
            preset.get('reasoning_effort') not in ('none', 'low', 'medium', 'high', 'xhigh')):
        raise ValueError('Invalid prepared native model metadata')
    if not preset['reason_modes'] and preset['reason_mode'] != 'off':
        raise ValueError('Unprepared author capability')
    for key in ('models_directory', 'pack_directory', 'mtp_directory'):
        value = preset.get(key)
        if not isinstance(value, str) or not value or ':' in value or value.startswith(('\\\\', '//')):
            raise ValueError('Invalid preset path')
        path = pathlib.Path(value)
        target = (root / path).absolute()
        if path.is_absolute() or '..' in path.parts or not target.is_relative_to(root.absolute()):
            raise ValueError('Preset path leaves installation')
        for parent in (target, *target.parents):
            if parent.exists() and (parent.is_symlink() or getattr(parent.lstat(), 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
                raise ValueError('Reparse preset path')
    if not isinstance(manifest.get('files'), list):
        raise ValueError('Pinned model file list required')
    for key, kind in [('native_file', 'model'), ('ple_file', 'model'), ('vision_file', 'vision')]:
        name = preset.get(key)
        if not isinstance(name, str) or ':' in name or pathlib.Path(name).name != name or not name.lower().endswith('.gguf'):
            raise ValueError('Invalid preset GGUF name')
        entries = [entry for entry in manifest['files'] if entry['kind'] == kind and entry['name'] == name]
        if len(entries) != 1:
            raise ValueError('Preset role does not name one pinned file')
    if preset['reason_modes']:
        first = next(entry for entry in manifest['files'] if entry['kind'] == 'model' and entry['name'] == preset['native_file'])
        if (not isinstance(first.get('repo'), str) or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', first['repo']) or
                not isinstance(first.get('revision'), str) or not re.fullmatch('[0-9a-f]{40}', first['revision']) or
                not isinstance(first.get('sha256'), str) or not re.fullmatch('[0-9a-f]{64}', first['sha256']) or
                preset.get('author_identity') != dict(repo=first['repo'], revision=first['revision'], main_sha256=first['sha256'])):
            raise ValueError('Author capability is not bound to pinned model')
    return preset


def make_config(root, models, manifest, workers, numa, port=8093):
    preset = native_preset(root, manifest)
    weights = [models / preset['native_file'], models / preset['ple_file']]
    projector = models / preset['vision_file']
    pack = root / preset['pack_directory']; mtp = root / preset['mtp_directory']
    env = dict(STRATA_NO_CPU_PIN='1', STRATA_ROUTE_TAIL_SKIP='0', STRATA_WIN_NUMA_NODE=str(numa),
        STRATA_DENSE_F32='1', STRATA_IQ_STAGE_TABLES='1', STRATA_IQ_STAGE_GRID_MMVQ='1',
        STRATA_QFUSE='1', STRATA_GR_NORM_FAST='1', STRATA_B6_MMVQ_ROWS='1', STRATA_EXPDEC='1',
        STRATA_EXPDEC_R='1', STRATA_DF_BRANCH='0', STRATA_PCIE_BALANCE='0', STRATA_SIDE_MIXER='0',
        STRATA_CKPT_PARK_REUSE='1', STRATA_PF_GROUP_SCRATCH='1', STRATA_POOL_FUSED='0', STRATA_POOL_GUIDED='0', STRATA_POOL_GUIDED_MIN='128', STRATA_ROUTE_PRIOR='0', STRATA_PCIE_FETCH_OVERLAP='1', STRATA_PCIE_STATIC_STAGE='1', STRATA_ARGMAX_ROWS='1', STRATA_MMVQ_EXACT_WARP='1', STRATA_KV_GROW='1', STRATA_Q8_SM60='1', STRATA_MTP_Q8_SM60='0')
    return dict(exe=str(root/'runtime/engine/strata.exe'), cwd=str(root/'app'), tokenizer=str(pack/'tokenizer'),
        args=['--pack',str(pack),'--native',str(weights[0]),'--ple-gguf',str(weights[1]),
              '--expert-profile',str(root/'app/data/expert-profile.bin'),'--expert-cache','auto',
              '--max-context','262144','--kv','q4_0','--kv-resident','20480','--kv-grow','--prefill','512','--pool-workers',str(workers),
              '--spec','3','--spec-min-p','0.5','--prompt-cache','6','--prompt-cache-every','16384',
              '--prompt-cache-root','2048','--vram-reserve-mib','150','--mtp',str(mtp),
              '--suffix-draft','3','--lookup-chain','0','--pcie-frac','1','--ple-io','ram','--adapt-async','1','--pool-tasks','0'],
        model_id=preset['model_id'], model_name=preset['model_name'], api_model_id=preset['model_name'], display_name=preset['display_name'],host='127.0.0.1',port=port,
        log=str(root/'logs/engine.log'),mtp=True,open_browser=False,env=env,
        reasoning_effort=preset['reasoning_effort'],reason_modes=preset['reason_modes'],reason_mode=preset['reason_mode'],sampling=dict(temperature=1.0,top_p=0.95,top_k=20,min_p=0.0,repetition_penalty=1.0,frequency_penalty=0.0),
        vision=dict(exe=str(root/'runtime/vision/strata-vision.exe'),model=str(weights[0]),mmproj=str(projector),
                    gpu=False,threads=8,max_tokens=300,require_ram=True))

def install(args):
    root = ROOT; bundle = check_bundle(root)
    if (root/'strata.json').exists():
        print('Existing profile retained. No weights downloaded. Run START.cmd, or extract another folder for another model/backend.')
        return
    if (root/'runtime/active.json').exists() or (root/'runtime/active.json').is_symlink():
        raise RuntimeError('Existing runtime state retained; restore its configuration or use another folder.')
    if getattr(args,'backend','native')!='native':
        return install_local(args,root,bundle)
    manifest = json.loads((root/'p40/model-downloads.json').read_text(encoding='utf8'))
    preset = native_preset(root, manifest)
    models = pathlib.Path(args.models_dir).expanduser().absolute() if args.models_dir else root/preset['models_directory']
    if (root/'strata.json').exists():
        print('Existing local configuration retained. Installer will not overwrite it.')
    (root/'logs').mkdir(exist_ok=True)
    needed = sum(e['size'] for e in manifest['files'])
    models.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(models).free < needed + (3 << 30):
        # Already downloaded data must not count against resumability.
        remaining = 0
        for e in manifest['files']:
            target = (root/preset['mtp_directory'] if e['kind']=='mtp' else models)/e['name']
            p = target if target.exists() else target.with_name(target.name+'.part')
            remaining += max(0, e['size'] - (p.stat().st_size if p.exists() else 0))
        if shutil.disk_usage(models).free < remaining + (3 << 30): raise RuntimeError('Not enough disk space for remaining weights and local pack')
    with install_lock(root):
        for e in manifest['files']:
            if e['repo'] not in manifest['allowed_repositories'] or len(e['revision']) != 40:
                raise RuntimeError('Unpinned download repository/revision')
            target = (root/preset['mtp_directory'] if e['kind']=='mtp' else models)/e['name']
            if pathlib.Path(e['name']).name != e['name']: raise RuntimeError('Unsafe download filename')
            fetch(e, target)
        pack = root/preset['pack_directory']; ready = pack/'.ready.json'; owner = pack/'.installer-owner.json'
        fingerprint = sha(root/'p40/model-downloads.json')
        first = next(e['name'] for e in manifest['files'] if e['kind']=='model')
        reuse = False
        if ready.exists():
            old = json.loads(ready.read_text()); reuse = old.get('downloads_sha256') == fingerprint and len(old.get('files',{})) >= 9
            reuse = reuse and all((pack/n).is_file() and sha(pack/n)==h for n,h in old.get('files',{}).items())
        if not reuse:
            if pack.exists() and any(pack.iterdir()) and not owner.exists(): raise RuntimeError('Unowned pack directory; preserved')
            atomic(owner, {'schema':1,'downloads_sha256':fingerprint})
            command = [sys.executable,'-I','-s','-B',str(root/'app/tools/iq_pack.py'),'--gguf',str(models/first),'--out',str(pack)]
            print('Building your own dense/tokenizer pack directly from the selected GGUF. No original checkpoint.', flush=True)
            result = subprocess.run(command,cwd=root/'app')
            if result.returncode: raise RuntimeError('Pack preparation failed; weights are preserved')
            names = ['dense.bin','index.txt','native_experts.txt','conversions.json','tokenizer/vocab.json',
                     'tokenizer/merges.txt','tokenizer/token_type.json','tokenizer/tokenizer.json','tokenizer/chat_template.jinja']
            if not all((pack/n).is_file() and (pack/n).stat().st_size for n in names): raise RuntimeError('Incomplete pack')
            atomic(ready, {'downloads_sha256':fingerprint,'files':{n:sha(pack/n) for n in names}})
        path = root/'strata.json'
        commit_initial_profile(root, make_config(root,models,manifest,args.workers,args.numa_node,args.port),
            dict(id=bundle['release_tag'],source='app',engine='runtime/engine/strata.exe',vision='runtime/vision/strata-vision.exe',source_sha=bundle['source_sha']))
    port=json.loads(path.read_text(encoding='utf8'))['port']
    print(f'Ready. Run START.cmd. API: http://127.0.0.1:{port}/v1. No API key is shipped or required for this localhost preset.')
    print('NUMA preference:',args.numa_node,'; choose node0 only after confirming your GPU is local to it.')

@contextlib.contextmanager
def private_runtime_path(root):
    """Only this installer process and its children; never changes the user's Windows environment."""
    runtime=(root/'runtime').resolve(strict=True);folders=[runtime/'engine',runtime/'vision']
    if (runtime/'backends').is_dir():folders.extend(p for p in sorted((runtime/'backends').iterdir()) if p.is_dir())
    for folder in folders:
        if folder.is_symlink() or not folder.resolve().is_relative_to(runtime):raise ValueError('Unsafe bundled runtime directory')
    before=os.environ.get('PATH','')
    try:
        os.environ['PATH']=os.pathsep.join(map(str,folders))+os.pathsep+before
        yield
    finally:os.environ['PATH']=before

def install_local(args,root,bundle):
    with private_runtime_path(root):return _install_local(args,root,bundle)

def _install_local(args,root,bundle):
    """One local-model setup for CPU/CUDA/Vulkan/Poly; no HF request or implicit MTP fallback."""
    if not args.model:raise ValueError('Choose a local GGUF with --model; only the prepared native preset downloads weights')
    config=root/'strata.json'
    if config.exists():raise ValueError('This installation already has a profile. Use another extracted folder; the existing profile is preserved')
    backend=args.backend;device_backend='cuda' if backend=='poly' else backend
    registry=json.loads((root/'p40/backends.json').read_text(encoding='utf8'))
    row=registry['engines'].get(backend)
    if not row:raise ValueError('Backend is absent from this package')
    engine=(root/row['path']).resolve(strict=True)
    if not engine.is_relative_to(root.resolve()) or sha(engine)!=row['sha256']:raise ValueError('Backend fingerprint mismatch')
    device=args.device
    if device_backend!='cpu' and not device:
        enumerator=engine if backend!='poly' else root/registry['engines']['cuda']['path']
        p=subprocess.run([str(enumerator),'--devices-json'],capture_output=True,text=True,encoding='utf8',timeout=60)
        if p.returncode:raise ValueError('Device detection failed; inspect driver installation, no driver or GPU setting was changed')
        devices=json.loads(p.stdout);prefix='Vulkan' if backend=='vulkan' else 'CUDA'
        choices=[x for x in devices if x['name'].startswith(prefix)]
        if len(choices)!=1:raise ValueError('Select --device explicitly from: '+', '.join(x['name']+' '+x['description'] for x in choices))
        device=choices[0]['name'];print('Selected device:',device,choices[0]['description'])
    module=root/'backends/prepare-profile.py'
    sys.path.insert(0,str(module.parent))
    spec=importlib.util.spec_from_file_location('strata_local_profile',module);prepared=importlib.util.module_from_spec(spec);spec.loader.exec_module(prepared)
    from gguf_meta import Header
    header=Header(args.model);limit=header.metadata.get(header.architecture+'.context_length')
    context=args.context or min(131072,limit if type(limit) is int else 131072)
    output=root/'profiles/local'
    with install_lock(root):
        # All validation precedes profile/config writes. The launcher proves exclusive port ownership before starting.
        report=prepared.prepare(args.model,engine,output,backend=device_backend,draft=args.draft_model,
            context=context,port=args.port,mtp=args.mtp,workers=args.workers,device=device,allow_native_api_port=True)
        value=json.loads((output/'profile.json').read_text(encoding='utf8'));value['cwd']=str(root/'app')
        value['log']=str(root/'logs/engine.log');value['open_browser']=False
        commit_initial_profile(root, value, dict(id=bundle['release_tag'],source='app',engine=row['path'],vision=None,
            source_sha=bundle['source_sha'],backend=backend,engine_sha256=row['sha256']))
        (root/'logs').mkdir(exist_ok=True)
    print(f'Ready: {backend}, {report["architecture"]}, MTP {args.mtp}. Run START.cmd; API http://127.0.0.1:{args.port}/v1')
    print('Local API key is generated in strata.json. No model downloaded. AUTOSTART.cmd enables independent startup.')

def interactive_choices(args):
    if args.backend is not None:return
    if not sys.stdin.isatty():args.backend='native';return
    registry=ROOT/'p40/backends.json'
    if registry.is_file() and not json.loads(registry.read_text(encoding='utf8')).get('engines'):
        print('This package contains the qualified native CUDA/P40 engine and CPU vision. Additional backend source is experimental; no other runtime is bundled.')
        args.backend='native'
        return
    print('Choose engine / Р вЂ™РЎвЂ№Р В±Р ВµРЎР‚Р С‘РЎвЂљР Вµ Р Т‘Р Р†Р С‘Р В¶Р С•Р С”:')
    print('1. Prepared native model РІР‚вЂќ CUDA/P40, resumable download / Р В·Р В°Р С–РЎР‚РЎС“Р В·Р С”Р В° РЎРѓ Р Т‘Р С•Р С”Р В°РЎвЂЎР С”Р С•Р в„–')
    print('2. Local GGUF РІР‚вЂќ CUDA NVIDIA; 3. Vulkan AMD Polaris/RX580; 4. CPU AVX1; 5. Poly CUDA')
    choice=input('[1-5, default1]: ').strip() or '1'
    modes={'1':'native','2':'cuda','3':'vulkan','4':'cpu','5':'poly'}
    if choice not in modes:raise ValueError('Choose1..5')
    args.backend=modes[choice]
    if args.backend!='native' and not args.model:args.model=input('Local GGUF path / Р СџРЎС“РЎвЂљРЎРЉ Р С” GGUF: ').strip().strip('"')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check-bundle',action='store_true',help='Verify package hashes only; no downloads, config edits or server')
    p.add_argument('--models-dir',help='Optional directory for GGUF/mmproj; default is inside the portable folder')
    p.add_argument('--workers',type=int,default=max(1,min(14,(os.cpu_count() or 2)-2)))
    p.add_argument('--port',type=int,default=8093,help='Local API port; choose a free port for a separate installation')
    p.add_argument('--numa-node',choices=['off','0','1'],default='off',help='Reference machine used node0; generic default leaves NUMA allocation unchanged')
    p.add_argument('--backend',choices=('native','cpu','cuda','vulkan','poly'),help='Prepared native model or an embedded local-GGUF engine')
    p.add_argument('--model',help='Existing local GGUF; never downloaded by a generic backend')
    p.add_argument('--draft-model',help='Existing matching NextN-head GGUF, when not embedded in the target')
    p.add_argument('--device',help='Explicit CUDA0 or Vulkan0; one available GPU may be detected automatically')
    p.add_argument('--context',type=int,help='Context up to the model metadata limit; generic KV starts at F16')
    p.add_argument('--mtp',choices=('require','off'),default='require',help='Require a trained compatible head; never silently disable MTP')
    args=p.parse_args()
    if args.check_bundle: check_bundle(); return 0
    interactive_choices(args)
    if os.name!='nt' or sys.maxsize<=2**32: p.error('Windows x64 required')
    if not 1<=args.workers<=256: p.error('workers must be1..256')
    if not 1024<=args.port<=65535 or args.port==8080: p.error('port must be1024..65535;8080 is reserved')
    if args.backend=='native' and any((args.model,args.draft_model,args.device,args.context,args.mtp=='off')):p.error('Native preset uses its pinned model/MTP/settings; use a local-GGUF backend for these options')
    install(args); return 0

if __name__=='__main__':
    try: raise SystemExit(main())
    except (RuntimeError,OSError,ValueError) as error:
        print('ERROR:',error,file=sys.stderr); raise SystemExit(1)
