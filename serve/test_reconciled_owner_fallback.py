"""New upstream fallback must respect the existing unknown-owner fence; no process/model launch."""
import unittest
from unittest import mock
from serve import server


class ReconciledFallback(unittest.TestCase):
    def test_unknown_previous_owner_never_enters_split_fallback(self):
        cfg={'args':['--pack','unused'],'split_fallback':{'exe':'other-unused','args':[]}}
        with mock.patch.object(server,'engine_args',return_value=[]), \
                mock.patch.object(server,'mtp_retry_args',return_value=None), \
                mock.patch.object(server,'StrataEngine',side_effect=server.EngineStuck('unconfirmed')) as start:
            with self.assertRaises(server.EngineStuck):
                server.start_engine_or_fallback(cfg,'unused',[],{},False,None)
            self.assertEqual(start.call_count,1)
