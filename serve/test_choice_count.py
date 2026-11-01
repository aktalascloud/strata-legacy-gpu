"""One supported OpenAI choice; refuse unsupported counts instead of silently returning one."""
import unittest
from serve.frontend import openai_to_messages

class ChoiceCount(unittest.TestCase):
    def test_default_and_single_choice_keep_conversion(self):
        req = {"messages": [{"role": "user", "content": "hello"}]}
        expected = openai_to_messages(req)
        for count in (None, 1):
            self.assertEqual(openai_to_messages({**req, "n": count}), expected)

    def test_other_counts_are_refused(self):
        for count in (False, True, 0, -1, 2, 1.0, "1", [], {}):
            with self.subTest(count=count), self.assertRaisesRegex(ValueError, '"n" must be 1'):
                openai_to_messages({"messages": [], "n": count})
