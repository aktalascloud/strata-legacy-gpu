"""Research queue metrics belong to the engine, not Service. No HTTP/native/GPU."""
from pathlib import Path
import unittest
from unittest import mock
from serve import server
from serve.frontend import ChatTemplate

class ParallelCounterMetrics(unittest.TestCase):
    def test_reads_engine_counters_and_supports_engine_without_them(self):
        tok = server.ByteTokenizer()
        engine = server.MockEngine(tok, "", max_context=16384)
        engine.batch = 2
        engine.par_counters = {"queued": 3, "queue_wait_s": 1.25}
        svc = server.Service(engine, tok, ChatTemplate(Path(__file__).parent / "chat_template.jinja"))
        with mock.patch.object(server, "PAR_COUNTERS", True):
            got = svc.metrics()["live"]["par_counters"]
            self.assertEqual(got, engine.par_counters)
            got["queued"] = 99
            self.assertEqual(engine.par_counters["queued"], 3)
            del engine.par_counters
            self.assertEqual(svc.metrics()["live"]["par_counters"], {})
