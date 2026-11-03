"""Owned child lifecycle contracts; no model, GPU, signals or process termination."""
import io
import ast
import subprocess
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from serve import server


class Pipe(io.StringIO):
    def close(self):
        if not self.closed:
            self.written = self.getvalue()
        super().close()


class Child:
    def __init__(self, stuck=False, exited=False):
        self.stdin, self.stdout = Pipe(), Pipe()
        self.returncode = 0 if exited else None
        self.stuck = stuck
        self.waits = 0

    def poll(self):
        return self.returncode

    def wait(self, timeout):
        self.waits += 1
        if self.stuck:
            raise subprocess.TimeoutExpired('owned-test-child', timeout)
        self.returncode = 0
        return 0

    def kill(self):
        raise AssertionError('force forbidden')

    terminate = kill


class GracefulExit(unittest.TestCase):
    def setUp(self):
        self.saved = set(server._unconfirmed_engine_exits)
        server._unconfirmed_engine_exits.clear()

    def tearDown(self):
        server._unconfirmed_engine_exits.clear()
        server._unconfirmed_engine_exits.update(self.saved)

    @staticmethod
    def engine(proc):
        e = server.StrataEngine.__new__(server.StrataEngine)
        e.proc, e.pump, e.log = proc, None, None
        e.ended = False
        return e

    def test_quit_eof_without_stop_or_force(self):
        p = Child(); e = self.engine(p)
        e.close()
        self.assertEqual(p.stdin.written, 'QUIT\n')
        self.assertTrue(p.stdout.closed)
        self.assertIsNone(e.proc)
        self.assertTrue(e.ended)
        self.assertFalse(server._unconfirmed_engine_exits)

    def test_timeout_preserves_handles_and_blocks_startup(self):
        p = Child(stuck=True); e = self.engine(p)
        self.assertTrue(e.alive())
        with self.assertRaises(server.EngineStuck): e.close()
        self.assertIs(e.proc, p)
        self.assertFalse(p.stdout.closed)
        self.assertFalse(e.ended)
        self.assertIn(p, server._unconfirmed_engine_exits)
        self.assertFalse(e.alive())             # retained ownership must not admit work through closed stdin
        with self.assertRaises(server.EngineStuck): server.end_leftover_engines('unused.exe')
        p.stuck = False
        e.close()
        self.assertIsNone(e.proc)
        self.assertEqual(p.waits, 2)
        self.assertFalse(server._unconfirmed_engine_exits)

    def test_exited_child_needs_no_command(self):
        p = Child(exited=True)
        server.graceful_engine_exit(p, 1)
        self.assertEqual(p.stdin.getvalue(), '')
        self.assertEqual(p.waits, 0)

    def test_failed_owner_guard_precedes_log_and_narrator_or_spawn(self):
        with patch.object(server, 'end_leftover_engines', side_effect=server.EngineStuck('unknown')), \
                patch('builtins.open', side_effect=AssertionError('log opened before owner guard')), \
                patch.object(server.threading, 'Thread', side_effect=AssertionError('thread before guard')), \
                patch.object(server, 'popen', side_effect=AssertionError('spawn before guard')):
            with self.assertRaises(server.EngineStuck):
                server.StrataEngine('unused.exe', ['--max-context', '64'], log='unused-test-log')

    def test_closed_pipe_still_waits_for_exit(self):
        p = Child(); p.stdin.close()
        server.graceful_engine_exit(p, 1)
        self.assertEqual(p.waits, 1)

    def test_actual_owned_python_child_observes_quit_and_eof(self):
        from serve import lifeline
        code="import sys;assert sys.stdin.readline()=='QUIT\\n';assert sys.stdin.read()=='';print('GRACEFUL_OK',flush=True)"
        with patch.object(lifeline.procs,'write_record',return_value=None):
            p=server.popen('cooperative lifecycle test',[sys.executable,'-I','-s','-B','-c',code],
                           stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            try:
                server.graceful_engine_exit(p,5)
                self.assertEqual(p.returncode,0)
                self.assertEqual(p.stdout.read().strip(),'GRACEFUL_OK')
                self.assertNotIn(p,server._unconfirmed_engine_exits)
            finally:
                server.graceful_engine_exit(p,5)
                p.stdout.close();p.stderr.close()

    def test_unknown_leftovers_refuse_without_signals_or_record_deletion(self):
        from strata_control import procs
        with patch.object(procs, 'leftovers', return_value=([], [{'pid': 123}])) as scan, \
                patch.object(procs, 'orphans_of', return_value=[]), \
                patch.object(procs, 'end_leftovers', side_effect=AssertionError('force forbidden')), \
                patch.object(procs, 'end_orphans', side_effect=AssertionError('force forbidden')):
            with self.assertRaises(server.EngineStuck): server.end_leftover_engines('unused.exe')
            scan.assert_called_once_with(forget_stale=False)
        with patch.object(procs, 'leftovers', side_effect=OSError('unreadable')):
            with self.assertRaises(server.EngineStuck): server.end_leftover_engines('unused.exe')

    def test_restart_does_not_retry_unconfirmed_constructor(self):
        e = self.engine(None)
        e.info, e.spawn = {}, ('unused.exe', [])
        with patch.object(server.StrataEngine, '__init__', side_effect=server.EngineStuck('pending')) as start:
            with self.assertRaises(server.EngineStuck): e.restart(tries=3)
            self.assertEqual(start.call_count, 1)
        self.assertFalse(e.starting)

    def test_vision_retains_owner_and_never_falls_back_while_stuck(self):
        v = server.Vision.__new__(server.Vision)
        p = Child(stuck=True)
        v.proc, v.stopped = p, False
        self.assertTrue(v.alive())
        with patch.object(v, '_start') as start:
            with self.assertRaises(server.EngineStuck): v.restart()
            start.assert_not_called()
        self.assertIs(v.proc, p)
        self.assertFalse(v.stopped)
        self.assertFalse(v.alive())
        v.fallback = ('unused-cpu-encoder', None, None)
        with patch.object(v, '_start_reader', side_effect=server.EngineStuck('pending')) as start:
            with self.assertRaises(server.EngineStuck): v._start()
            self.assertEqual(start.call_count, 1)
        p.stuck = False
        v.close()
        self.assertIsNone(v.proc)
        self.assertTrue(v.stopped)

    def test_graceful_lifeline_omits_job_watcher_and_atexit_force_list(self):
        from serve import lifeline
        p = Child(); p.pid = 123456
        with patch.object(lifeline.subprocess, 'Popen', return_value=p) as spawn, \
                patch.object(lifeline, 'mechanism', side_effect=AssertionError('no forced lifetime')), \
                patch.object(lifeline.winjob, 'contain', side_effect=AssertionError('no job')), \
                patch.object(lifeline, '_watch', side_effect=AssertionError('no watcher')), \
                patch.object(lifeline.procs, 'write_record', return_value=None) as record, \
                patch.object(lifeline.threading, 'Thread'):
            self.assertIs(lifeline.popen(['owned-test-child'], 'engine', graceful_only=True), p)
            record.assert_called_once()
            self.assertNotIn(p, lifeline._children)
            self.assertNotIn('graceful_only', spawn.call_args.kwargs)

    def test_server_has_no_direct_force_calls(self):
        tree = ast.parse(Path(server.__file__).read_text('utf-8'))
        calls = [n.func.attr for n in ast.walk(tree) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Attribute) and n.func.attr in ('kill', 'terminate')]
        self.assertEqual(calls, [])

    def test_shutdown_waits_after_deadline_without_cancelling_accepted_calls(self):
        tree = ast.parse(Path(server.__file__).read_text('utf-8'))
        main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
        final = next(n.finalbody for n in main.body if isinstance(n, ast.Try) and n.finalbody
                     and isinstance(n.finalbody[0], ast.Assign)
                     and n.finalbody[0].targets[0].id == 'cancelled')
        stop = next(i for i, n in enumerate(final) if isinstance(n, ast.Assign)
                    and isinstance(n.targets[0], ast.Name) and n.targets[0].id == 'closers')
        module = ast.Module(body=final[:stop], type_ignores=[])
        calls = []
        class Service:
            instance_id = 'owned-test'
            def begin_drain(self): calls.append('drain'); return 1
            def wait_for_drain(self, timeout):
                calls.append(('wait', timeout))
                return 1 if len(calls) == 2 else 0
            def cancel_owned_requests(self): raise AssertionError('accepted call cancelled')
        env = {'svc': Service(), 'a': SimpleNamespace(shutdown_timeout=0),
               'notify_lifecycle': lambda *args: None, 'print': lambda *args, **kwargs: None}
        exec(compile(ast.fix_missing_locations(module), '<actual shutdown drain>', 'exec'), env)
        self.assertEqual(calls, ['drain', ('wait', 0), ('wait', 1.0)])
        self.assertEqual(env['pending'], 0)
        self.assertEqual(env['cancelled'], 0)


if __name__ == '__main__':
    unittest.main()
