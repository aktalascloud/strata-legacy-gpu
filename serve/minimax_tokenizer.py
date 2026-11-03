"""MiniMax NFC/split adapter over the unchanged qualified core tokenizer."""
import unicodedata
import regex
from tools.strata_tokenizer import Tokenizer as CoreTokenizer

MINIMAX_PATTERN = "[^\\r\\n\\p{L}\\p{N}]?[\\p{Lu}\\p{Lt}\\p{Lm}\\p{Lo}\\p{M}]*[\\p{Ll}\\p{Lm}\\p{Lo}\\p{M}]+(?i:'s|'t|'re|'ve|'m|'ll|'d)?|[^\\r\\n\\p{L}\\p{N}]?[\\p{Lu}\\p{Lt}\\p{Lm}\\p{Lo}\\p{M}]+[\\p{Ll}\\p{Lm}\\p{Lo}\\p{M}]*(?i:'s|'t|'re|'ve|'m|'ll|'d)?|\\p{N}{1,3}| ?[^\\s\\p{L}\\p{N}]+[\\r\\n/]*|\\s*[\\r\\n]+|\\s+(?!\\S)|\\s+"

class Tokenizer(CoreTokenizer):
    def __init__(self,tokens,merges,token_types=None,pre="minimax",special_ids=None):
        if pre!="minimax":raise ValueError("MiniMax tokenizer adapter requires its canonical pre identity")
        super().__init__(tokens,merges,token_types,"qwen35",special_ids)
        self.pre="minimax"
        self._re=regex.compile(MINIMAX_PATTERN)
        self._split=self._re.findall

    def _encode_plain(self,text):
        return super()._encode_plain(unicodedata.normalize("NFC",text))
