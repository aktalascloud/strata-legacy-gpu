"""Deterministic ownership races, without a model or GPU."""
import unittest
import sys
import threading
from types import SimpleNamespace
from unittest.mock import patch

from serve import server
from serve.test_graceful_engine_exit import Child, Pipe, GracefulExit


class StartCloseRace(unittest.TestCase):
    def constructor_closed_by_reader(self, ready=False):
        engine = server.StrataEngine.__new__(server.StrataEngine)
        child = Child(exited=True)
        if ready:
            child.stdout.write('READY 64 stop\n')
            child.stdout.seek(0)
        def thread(target, args=(), **kw):
            def start():
                self.assertIs(target, server.StrataEngine._ready_pump)
                if ready:
                    target(*args)
                    engine.close()
                else:
                    engine.close()
                    target(*args)
            return SimpleNamespace(start=start)
        with patch.object(server, 'end_leftover_engines'), \
                patch.object(server, 'popen', return_value=child) as spawn, \
                patch.object(server.threading, 'Thread', side_effect=thread), \
                patch.object(server, 'transient_start_failure', return_value=True) as retry:
            with self.assertRaises(server.EngineDied):
                server.StrataEngine.__init__(engine, 'unused.exe', ['--max-context', '64'])
            spawn.assert_called_once()
            retry.assert_not_called()  # An intentional concurrent close must not start a replacement.
        self.assertIsNone(engine.proc)
        self.assertTrue(child.stdin.closed and child.stdout.closed)

    def test_closed_before_ready_keeps_exact_process_handle(self):
        self.constructor_closed_by_reader()

    def test_closed_after_ready_is_not_published_as_alive(self):
        self.constructor_closed_by_reader(ready=True)

    def test_second_closer_can_clear_shared_handle(self):
        child = Child()
        engine = GracefulExit.engine(child)
        def concurrent_close(proc, timeout):
            self.assertIs(proc, child)
            proc.returncode = 0
            engine.proc, engine.ended = None, True
        with patch.object(server, 'graceful_engine_exit', side_effect=concurrent_close):
            engine.close()
        self.assertIsNone(engine.proc)
        self.assertTrue(child.stdin.closed and child.stdout.closed)

    def test_old_close_never_clears_replacement_or_its_log(self):
        child, replacement = Child(), Child()
        old_log, new_log = Pipe(), Pipe()
        engine = GracefulExit.engine(child)
        engine.log = old_log
        def replaced(proc, timeout):
            self.assertIs(proc, child)
            proc.returncode = 0
            engine.proc, engine.log = replacement, new_log
        with patch.object(server, 'graceful_engine_exit', side_effect=replaced):
            engine.close()
        self.assertIs(engine.proc, replacement)
        self.assertFalse(engine.ended)
        self.assertTrue(child.stdin.closed and child.stdout.closed and old_log.closed)
        self.assertFalse(replacement.stdin.closed or replacement.stdout.closed or new_log.closed)

    def test_close_during_retry_delay_prevents_new_spawn(self):
        engine = server.StrataEngine.__new__(server.StrataEngine)
        child = Child(exited=True)
        def thread(target, args=(), **kw):
            return SimpleNamespace(start=lambda: target(*args))
        with patch.object(server, 'end_leftover_engines'), \
                patch.object(server, 'popen', return_value=child) as spawn, \
                patch.object(server.threading, 'Thread', side_effect=thread), \
                patch.object(server, 'transient_start_failure', return_value=True), \
                patch.object(server.time, 'sleep', side_effect=lambda _: engine.close()):
            with self.assertRaisesRegex(server.EngineDied, 'closed while waiting to retry'):
                server.StrataEngine.__init__(engine, 'unused.exe', ['--max-context', '64'])
            spawn.assert_called_once()

    def test_real_child_closed_during_constructor_observes_quit_and_eof(self):
        engine = server.StrataEngine.__new__(server.StrataEngine)
        reader_started, release_reader = threading.Event(), threading.Event()
        errors, owned = [], []
        real_spawn, real_ready = server.popen, server.StrataEngine._ready_pump
        code = "import sys;assert sys.stdin.readline()=='QUIT\\n';assert sys.stdin.read()==''"
        def spawn(what, args, **kw):
            child = real_spawn(what, [sys.executable, '-I', '-s', '-B', '-c', code], **kw)
            owned.append(child)
            return child
        def ready(proc, out):
            reader_started.set()
            release_reader.wait(5)
            real_ready(proc, out)
        def start():
            try:
                server.StrataEngine.__init__(engine, 'owned-constructor-race', ['--max-context', '64'])
            except Exception as error:
                errors.append(error)
        with patch.object(server, 'end_leftover_engines'), \
                patch.object(server.lifeline.procs, 'write_record', return_value=None), \
                patch.object(server, 'popen', side_effect=spawn), \
                patch.object(server.StrataEngine, '_ready_pump', staticmethod(ready)), \
                patch.object(server, 'ENGINE_READY_S', 5), patch.object(server, 'ENGINE_QUIT_WAIT_S', 5):
            thread = threading.Thread(target=start)
            thread.start()
            try:
                self.assertTrue(reader_started.wait(5))
                engine.close()
            finally:
                release_reader.set()
                for child in owned:
                    server.graceful_engine_exit(child, 5)
                thread.join(5)
        self.assertFalse(thread.is_alive())
        self.assertEqual(len(owned), 1)
        self.assertEqual(owned[0].returncode, 0)
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], server.EngineDied)
        self.assertIsNone(engine.proc)
        self.assertNotIn(owned[0], server._unconfirmed_engine_exits)


if __name__ == '__main__':
    unittest.main()
