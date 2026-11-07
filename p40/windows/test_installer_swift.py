"""First-install profile checks without weights, downloads, tasks or a server."""
import copy
import importlib.util
import json
import tempfile
from pathlib import Path

def main():
    folder=Path(__file__).resolve().parent
    spec=importlib.util.spec_from_file_location('strata_installer',folder/'installer.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    manifest=json.loads((folder.parent/'model-downloads.json').read_text())
    with tempfile.TemporaryDirectory(prefix='strata profile ') as temporary:
        root=Path(temporary)
        config=module.make_config(root,root/'models',manifest,14,'off')
        args=config['args'];value=lambda flag:args[args.index(flag)+1]
        assert value('--max-context')=='262144' and value('--vram-reserve-mib')=='150'
        assert value('--kv-resident')=='20480' and '--kv-grow' in args
        assert value('--spec-min-p')=='0.5' and value('--suffix-draft')=='3'
        assert config['model_id']=='Swift' and config['reason_modes'] is False and config['reason_mode']=='off'
        assert config['reasoning_effort']=='xhigh' and config['vision']['gpu'] is False
        assert config['vision']['require_ram'] is True
        assert config['sampling']['temperature']==1.0 and config['sampling']['top_p']==0.95
        assert config['env']['STRATA_MMVQ_EXACT_WARP']=='1'
        assert config['env']['STRATA_SM61_EXPERT_TABLE']=='1'
        bad=copy.deepcopy(manifest);bad['native_preset']['pack_directory']='../escape'
        try:module.make_config(root,root/'models',bad,14,'off')
        except ValueError:pass
        else:raise AssertionError('Traversal accepted')
        assert not (root/'strata.json').exists() and not (root/'runtime').exists()
    print('Swift first-install profile: passed; no downloads, config writes or tasks.')

if __name__=='__main__':main()
