import json
from pathlib import Path
import tempfile
import unittest

from serve.server import clean_shared_defaults, load_shared_settings


class LoadSharedSettings(unittest.TestCase):
    def load(self, text):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            path = Path(directory) / 'fixture.json'
            if text is not None:
                path.write_text(text, encoding='utf-8')
            messages = []
            result = load_shared_settings(path, warn=messages.append)
            return result, messages

    def test_unknown_key_retains_other_valid_defaults(self):
        good = {'reasoning_effort': 'xhigh', 'temperature': 0.8, 'top_p': 0.95}
        result, messages = self.load(json.dumps(dict(good, unknown_future_setting=False)))
        self.assertEqual(result, good)
        self.assertEqual(len(messages), 1)
        self.assertIn('unknown_future_setting', messages[0])

    def test_bad_values_including_overflow_do_not_discard_good_keys(self):
        result, messages = self.load('{"reasoning_effort":"xhigh","top_p":5,"top_k":Infinity}')
        self.assertEqual(result, {'reasoning_effort': 'xhigh'})
        self.assertEqual(len(messages), 2)

    def test_unparseable_and_nonobject_files_are_reported(self):
        for text in ('{bad json', '[]', 'null'):
            with self.subTest(text=text):
                result, messages = self.load(text)
                self.assertEqual(result, {})
                self.assertEqual(len(messages), 1)

    def test_missing_file_is_quiet(self):
        self.assertEqual(self.load(None), ({}, []))

    def test_valid_file_matches_existing_strict_reader(self):
        fixture = {'reasoning_effort':'xhigh', 'reason_mode':'off', 'reasoning_budget_tokens':0,
                   'temperature':0.8, 'top_p':0.95, 'top_k':20, 'seed':42, 'max_tokens':32,
                   'experimental_speed_projection':False}
        result, messages = self.load(json.dumps(fixture))
        self.assertEqual(result, clean_shared_defaults(fixture))
        self.assertEqual(messages, [])

    def test_strict_POST_validator_still_rejects_entire_invalid_body(self):
        with self.assertRaises(ValueError):
            clean_shared_defaults({'reasoning_effort':'xhigh', 'unknown_future_setting':False})
        with self.assertRaises(ValueError):
            clean_shared_defaults({'reasoning_effort':'xhigh', 'top_p':5})
