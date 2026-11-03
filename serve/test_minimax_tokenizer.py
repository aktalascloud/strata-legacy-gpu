"""MiniMax-only splitter/NFC delta; no weights, inference or optional runtime installs."""
import unittest

from tools.strata_tokenizer import BYTE_TO_UNICODE, PromptEncoder, Tokenizer as CoreTokenizer
from serve.minimax_tokenizer import Tokenizer


def tokenizer(pre="minimax"):
    tokens = [BYTE_TO_UNICODE[i] for i in range(256)] + ["]~b]", "<mm:think>", "</mm:think>"]
    return (Tokenizer if pre=="minimax" else CoreTokenizer)(tokens, [], [1] * 256 + [3] * 3, pre=pre)


class MiniMaxTokenizer(unittest.TestCase):
    def test_model_split_rules(self):
        tok = tokenizer()
        self.assertEqual(tok._split("abcDEF"), ["abc", "DEF"])
        self.assertEqual(tok._split("1234567"), ["123", "456", "7"])
        self.assertEqual(tok._split("DON'T"), ["DON'T"])

    def test_plain_segments_are_nfc(self):
        tok = tokenizer()
        self.assertEqual(tok.decode(tok.encode("e\u0301 a\u0308")), "é ä")

    def test_added_tokens_bound_normalization(self):
        tok = tokenizer()
        ids = tok.encode("e\u0301<mm:think>a\u0308", parse_special=True)
        self.assertIn(257, ids)
        self.assertEqual(tok.decode(ids), "é<mm:think>ä")

    def test_literal_control_span_stays_plain(self):
        tok = tokenizer()
        text = "e\u0301]~b]a\u0308"
        ids = tok.encode(text, parse_special=True, plain=[(2, 6)])
        self.assertNotIn(256, ids)
        self.assertEqual(tok.decode(ids), "é]~b]ä")

    def test_incremental_append_and_normalization_edit(self):
        tok = tokenizer()
        encoder = PromptEncoder(tok)
        base = "]~b]" + "e\u0301 " * 20 + "<mm:think>" + "a\u0308 " * 20
        for text in (base, base + "next", base.replace("e\u0301", "e\u0300", 1), base + "]~b]e\u0301"):
            self.assertEqual(encoder.encode(text), tok.encode(text, parse_special=True))

    def test_existing_qwen_keeps_raw_unicode(self):
        raw = "e\u0301"
        self.assertEqual(tokenizer("qwen35").decode(tokenizer("qwen35").encode(raw)), raw)


if __name__ == "__main__":
    unittest.main()
