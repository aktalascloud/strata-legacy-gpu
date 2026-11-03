"""A damaged launch profile must not hide another launch or its saved key. No real profiles or keys."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from strata_cli.launch import access, cmd


class ProfileFaultIsolation(unittest.TestCase):
    def test_broken_profile_before_or_after_valid_profile_is_skipped(self):
        good = {"source_config": "C:/fixture/own.json", "overrides": {"port": 8199}}
        def load(name):
            if name == "launch-bad":
                raise ValueError("invalid overrides")
            return good, "revision"
        for names in (("bad", "good"), ("good", "bad")):
            with self.subTest(names=names), \
                 mock.patch("strata_control.profiles.list_profiles", return_value=[{"id": "launch-" + n} for n in names]), \
                 mock.patch("strata_control.profiles.load", side_effect=load), \
                 mock.patch("strata_control.runtime.status", return_value={"state": "ready"}):
                rows = cmd.running_launches()
            self.assertEqual([(r["name"], r["config"], r["port"]) for r in rows], [("good", good["source_config"], 8199)])

    def test_error_row_does_not_hide_valid_saved_key(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "fixture.json"
            config.write_text(json.dumps({"api_key": "fixture-only-key"}), encoding="utf-8")
            bad = {"id": "launch-bad", "error": "invalid JSON"}
            good = {"id": "launch-good", "source_config": str(config)}
            for rows in ([bad, good], [good, bad]):
                with mock.patch("strata_control.profiles.list_profiles", return_value=rows):
                    self.assertEqual(access.kept_key(), "fixture-only-key")


if __name__ == "__main__":
    unittest.main()
