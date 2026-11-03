"""PR4831 client hang-up handling; shutdown still drains without cancellation."""
import contextlib
import io
import json
import socket
import threading
import time
from serve.server import MockEngine
from serve.test_responses import Server

class HeldEngine(MockEngine):
    """Says `tokens` of its script, then holds the answer open until the request is cancelled or released."""
    tokens = 5

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.holding, self.release = threading.Event(), threading.Event()

    def generate(self, ids, max_new, sampling, cancel, embeddings=None):
        yield from self.script[:self.tokens]
        self.holding.set()
        while not (cancel.is_set() or self.release.is_set()):
            time.sleep(0.01)
        if not cancel.is_set():
            yield from self.script[self.tokens:]


class ClientCancellation(Server):
    script = "</think>\n\nThe file says before."
    body = {"input": "hi", "reasoning": {"effort": "none"}}

    def setUp(self):
        super().setUp()
        self.engine = self.svc.engine = HeldEngine(self.tok, self.script, max_context=16384)


    def test_a_request_that_ends_within_the_drain_is_answered(self):
        def stop():
            self.engine.holding.wait(30)
            self.svc.begin_drain()
            self.engine.release.set()
        t = threading.Thread(target=stop)
        t.start()
        code, r = self.post(self.body)
        t.join()
        self.assertEqual((code, r["status"]), (200, "completed"), r)


    def hang_up(self, draining):
        """A client sends a request and closes its socket while the engine holds it; the watcher cancels it within
        0.5 s.  -> (what the server logged, the state in the monitor)."""
        self.svc.api_monitor = True
        data = json.dumps(self.body).encode()
        log = io.StringIO()
        with contextlib.redirect_stdout(log):
            with socket.create_connection(("127.0.0.1", self.port), timeout=30) as s:
                s.sendall(b"POST /v1/responses HTTP/1.1\r\nContent-Type: application/json\r\n"
                          b"Content-Length: %d\r\n\r\n" % len(data) + data)
                self.assertTrue(self.engine.holding.wait(30))
                if draining:
                    self.svc.begin_drain()
            self.assertEqual(self.svc.wait_for_drain(30), 0)
            deadline = time.monotonic() + 30             # the record closes just after the call is released
            while "finished_at" not in self.svc.request_records()[0] and time.monotonic() < deadline:
                time.sleep(0.01)
        return log.getvalue(), self.svc.request_records()[0]["state"]


    def test_a_client_that_hangs_up_is_a_disconnect_not_a_malformed_request(self):
        log, state = self.hang_up(draining=False)
        self.assertNotIn("malformed", log)
        self.assertNotIn("Traceback", log)
        self.assertEqual(state, "disconnected")


    def test_a_client_that_hangs_up_during_a_drain(self):
        log, state = self.hang_up(draining=True)
        self.assertNotIn("malformed", log)
        self.assertNotIn("Traceback", log)
        self.assertEqual(state, "disconnected")                 # the 503 nobody reads: known, and named in the pull request
