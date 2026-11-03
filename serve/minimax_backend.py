"""MiniMax serving CLI/READY contracts. These checks do not qualify weights or start processes."""
from __future__ import annotations
import math

_VALUES = frozenset(('--pack', '--gpus', '--max-context', '--cpu-threads', '--reserve-gb', '--chunk',
    '--staging', '--resident-cap', '--profile', '--expert-profile', '--tp', '--cache-gb', '--layer-split',
    '--kv-cache', '--kv-streaming', '--kv-resident', '--kv-rot', '--kv-rotate', '--dspark', '--dspark-conf',
    '--dspark-cost', '--parallel', '--tp-chunk', '--tp-ffn-rows', '--prefill-gemm', '--prefill-tune', '--vision'))
_SWITCHES = frozenset(('--no-pin-pool', '--no-fast-decode', '--no-promote', '--no-prefill-tune'))
_ALIASES = {'--kv-rotate': '--kv-rot'}


def options(args):
    if not isinstance(args, list) or not args or not all(isinstance(x, str) and x and '\0' not in x for x in args):
        raise ValueError('MiniMax argv must be separate nonempty strings')
    found = {}
    at = 0
    while at < len(args):
        name = args[at]
        key = _ALIASES.get(name, name)
        if name not in _VALUES | _SWITCHES:
            raise ValueError('unsupported MiniMax serving argument: ' + name)
        if key in found:
            raise ValueError('duplicate MiniMax argument: ' + key)
        if name in _VALUES:
            if at + 1 == len(args) or args[at + 1].startswith('--'):
                raise ValueError('MiniMax argument needs a value: ' + name)
            found[key] = args[at + 1]
            at += 2
        else:
            found[key] = True
            at += 1
    return found


def checked_args(cfg):
    if cfg.get('engine_kind') != 'mm3' or cfg.get('backend') != 'cuda' or cfg.get('model_arch') != 'minimax-m3':
        raise ValueError('MiniMax requires its explicit CUDA backend/architecture profile')
    if any(cfg.get(k) for k in ('user_args', 'layer_split', 'replicas', 'gpu_groups')) or cfg.get('parallel') not in (None, 1):
        raise ValueError('Qwen overrides and parallel profiles are not MiniMax DSpark settings')
    if cfg.get('vision'):
        raise ValueError('MiniMax needs its own qualified vision path; an existing Qwen encoder cannot be reused')
    args = cfg.get('args')
    parsed = options(args)
    for name in ('--pack', '--max-context', '--cpu-threads', '--reserve-gb', '--kv-cache', '--kv-streaming', '--dspark'):
        if name not in parsed:
            raise ValueError('MiniMax profile must explicitly select ' + name)
    for name in ('--max-context', '--cpu-threads', '--chunk', '--staging', '--resident-cap', '--kv-resident', '--tp-chunk', '--tp-ffn-rows'):
        if name not in parsed:
            continue
        try:
            value = int(parsed[name])
        except ValueError:
            raise ValueError('invalid MiniMax integer: ' + name) from None
        if value < (0 if name in ('--resident-cap', '--kv-resident') else 1):
            raise ValueError('invalid MiniMax integer range: ' + name)
    for name in ('--reserve-gb', '--cache-gb', '--dspark-conf', '--dspark-cost'):
        if name not in parsed:
            continue
        try:
            value = float(parsed[name])
        except ValueError:
            raise ValueError('invalid MiniMax number: ' + name) from None
        if not math.isfinite(value) or value < 0 or name == '--dspark-conf' and value > 1:
            raise ValueError('invalid MiniMax number range: ' + name)
    if parsed.get('--parallel', '1') != '1':
        raise ValueError('parallel MiniMax conversations disable DSpark; no silent fallback')
    if parsed.get('--vision', 'off') != 'off':
        raise ValueError('MiniMax vision is not qualified by this text/DSpark profile')
    if parsed['--kv-cache'] not in ('bf16', 'int8', 'fp8', 'fp4'):
        raise ValueError('unknown native MiniMax KV format; q4_0 must not be relabeled as fp4')
    if parsed['--kv-streaming'] not in ('on', 'off'):
        raise ValueError('MiniMax KV streaming must be on/off')
    if parsed['--kv-streaming'] == 'on' and '--kv-resident' not in parsed:
        raise ValueError('MiniMax KV streaming needs explicit resident size')
    policy = cfg.get('mtp_policy')
    if policy not in ('require', 'off') or parsed['--dspark'] != ('on' if policy == 'require' else 'off'):
        raise ValueError('MiniMax MTP policy and native DSpark argument disagree')
    if cfg.get('drafting') not in (None, 'auto', 'mtp', 'off') or cfg.get('mtp') is False and policy == 'require':
        raise ValueError('foreign drafter/override contradicts MiniMax DSpark policy')
    if cfg.get('drafting') == 'off' and policy == 'require' or cfg.get('drafting') == 'mtp' and policy == 'off' or cfg.get('mtp') is True and policy == 'off':
        raise ValueError('MiniMax drafting override contradicts its policy')
    return list(args)


def validate_ready(info, args, context):
    """Check loaded facts before calling a required-DSpark model ready; caller must drain on failure."""
    parsed = options(args)
    if info.get('engine_kind') != 'mm3':
        raise ValueError('the selected engine did not identify as MiniMax')
    if parsed.get('--dspark') == 'on' and info.get('dspark') not in (1, '1'):
        raise ValueError('required MiniMax DSpark was not loaded')
    if parsed.get('--dspark') == 'off' and info.get('dspark') not in (0, '0'):
        raise ValueError('MiniMax DSpark facts contradict off policy')
    if '--max-context' in parsed and int(parsed['--max-context']) != context:
        raise ValueError('MiniMax context changed from the explicitly selected value')
    if '--no-pin-pool' not in parsed:
        counts = [info.get(key) for key in ('experts', 'expert_slots', 'ram_slots')]
        if any(type(value) is not int or value < 0 for value in counts):
            raise ValueError('MiniMax host RAM pool counts are missing or invalid')
        if counts[1] + counts[2] != counts[0]:
            raise ValueError('MiniMax host RAM pool is incomplete; disk fallback is not allowed')
