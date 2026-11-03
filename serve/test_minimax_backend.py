"""Pure CLI/READY/sampling contracts, no process or model startup."""
import unittest
from unittest.mock import patch
from serve.minimax_backend import checked_args, validate_ready
from serve import server
from serve.server import StrataEngine
from serve.test_graceful_engine_exit import Child


def profile():
    return {'engine_kind': 'mm3', 'backend': 'cuda', 'model_arch': 'minimax-m3', 'mtp_policy': 'require',
            'args': ['--pack', 'pack', '--max-context', '262144', '--cpu-threads', '15', '--reserve-gb', '0.146484375',
                     '--kv-cache', 'fp4', '--kv-streaming', 'on', '--kv-resident', '20480', '--dspark', 'on']}


class MiniMaxBackend(unittest.TestCase):
    def test_native_profile_and_no_mutation(self):
        cfg = profile();before = list(cfg['args'])
        self.assertEqual(checked_args(cfg), before)
        self.assertEqual(cfg['args'], before)

    def test_foreign_flags_duplicate_and_unsupported_kv_reject(self):
        for extra in (['--mtp', 'head'], ['--serve'], ['--max-context', '32768'], ['--parallel', '2']):
            cfg = profile();cfg['args'] += extra
            with self.assertRaises(ValueError):checked_args(cfg)
        cfg = profile();cfg['args'][cfg['args'].index('fp4')] = 'q4_0'
        with self.assertRaises(ValueError):checked_args(cfg)

    def test_required_draft_and_foreign_vision_reject(self):
        cfg = profile();cfg['args'][-1] = 'off'
        with self.assertRaises(ValueError):checked_args(cfg)
        cfg = profile();cfg['vision'] = {'exe': 'a-qwen-encoder'}
        with self.assertRaises(ValueError):checked_args(cfg)

    def test_ready_requires_actual_draft_and_context(self):
        args = profile()['args']
        validate_ready({'engine_kind': 'mm3', 'dspark': 1, 'experts': 3, 'expert_slots': 1, 'ram_slots': 2}, args, 262144)
        for info, context in (({'engine_kind': 'mm3', 'dspark': 0}, 262144),
                              ({'engine_kind': 'qwen', 'dspark': 1}, 262144),
                              ({'engine_kind': 'mm3', 'dspark': 1}, 32768)):
            with self.assertRaises(ValueError):validate_ready(info, args, context)

    def test_ready_full_ram_pool_or_explicit_legacy_no_pin_pool(self):
        info = {'engine_kind': 'mm3', 'dspark': 1, 'experts': 10, 'expert_slots': 3, 'ram_slots': 7}
        args = profile()['args']
        validate_ready(info, args, 262144)
        validate_ready({'engine_kind': 'mm3', 'dspark': 1}, args + ['--no-pin-pool'], 262144)

    def test_ready_rejects_partial_missing_and_invalid_ram_pool(self):
        base = {'engine_kind': 'mm3', 'dspark': 1, 'experts': 10, 'expert_slots': 3, 'ram_slots': 7}
        for update in ({'ram_slots': 6}, {'ram_slots': None}, {'ram_slots': -1}, {'ram_slots': '7'},
                       {'ram_slots': True}, {'expert_slots': -1}, {'experts': None}, {'expert_slots': 11}):
            with self.subTest(update=update), self.assertRaises(ValueError):
                validate_ready({**base, **update}, profile()['args'], 262144)

    def test_constructor_incomplete_ram_pool_is_drained_before_failure(self):
        p = Child()
        p.stdout.write('INFO engine=mm3 engine_kind=mm3 dspark=1 experts=10 expert_slots=3 ram_slots=6\nREADY 262144 stop\n')
        p.stdout.seek(0)
        with patch.object(server, 'end_leftover_engines'), patch.object(server, 'popen', return_value=p):
            with self.assertRaisesRegex(server.EngineDied, 'host RAM pool is incomplete'):
                StrataEngine('unused.exe', profile()['args'], expected_kind='mm3')
        self.assertEqual(p.stdin.written, 'QUIT\n')
        self.assertIsNotNone(p.poll())
        self.assertTrue(p.stdout.closed)

    def test_sampling_zero_and_wide_k_are_preserved(self):
        engine = StrataEngine.__new__(StrataEngine);engine.info = {'engine_kind': 'mm3'}
        for k in (0, 1000):
            wire = engine.request_sampling({'temperature': 0, 'top_k': k, 'seed': 119})
            self.assertIn(' temperature=0.0', wire)
            self.assertIn(' top_k=' + str(k), wire)
        engine.info = {}
        self.assertEqual(engine.request_sampling({'top_k': 1000}), StrataEngine.sampling_keys({'top_k': 1000}))

    def test_factory_and_no_foreign_saved_tuning_or_tail_role(self):
        cfg = profile()
        self.assertEqual(server.engine_args(cfg), cfg['args'])
        with patch('strata_control.presets.overlay', side_effect=AssertionError('foreign tuning')):
            self.assertIs(server.apply_saved_tuning(cfg), cfg)
        self.assertIsNone(server.effort_end_args(cfg, 'unused', None))
        cfg['effort_position'] = 'end'
        with self.assertRaises(ValueError): server.effort_end_args(cfg, 'unused', None)

    def test_actual_constructor_rejects_silent_dspark_fallback_and_stops_gracefully(self):
        p = Child()
        p.stdout.write('INFO engine=mm3 engine_kind=mm3 dspark=0\nREADY 262144 stop\n')
        p.stdout.seek(0)
        with patch.object(server, 'end_leftover_engines'), patch.object(server, 'popen', return_value=p):
            with self.assertRaisesRegex(server.EngineDied, 'DSpark was not loaded'):
                StrataEngine('unused.exe', profile()['args'], expected_kind='mm3')
        self.assertEqual(p.stdin.written, 'QUIT\n')
        self.assertIsNotNone(p.poll())
        self.assertTrue(p.stdout.closed)

    def test_failed_constructor_cannot_lose_a_still_running_child(self):
        p = Child(stuck=True)
        try:
            with patch.object(server, 'end_leftover_engines'), patch.object(server, 'popen', return_value=p) as spawn:
                with self.assertRaises(server.EngineStuck):
                    StrataEngine('unused.exe', profile()['args'], expected_kind='mm3')
                self.assertEqual(spawn.call_count, 1)
            self.assertIn(p, server._unconfirmed_engine_exits)
            self.assertFalse(p.stdout.closed)
            with self.assertRaises(server.EngineStuck): server.end_leftover_engines('unused.exe')
        finally:
            p.stuck = False
            server.graceful_engine_exit(p, 1)
            p.stdout.close()


if __name__ == '__main__':unittest.main()
