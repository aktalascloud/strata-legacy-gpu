"""Replay main's actual family initialization, not a hand-initialized MiniMax Service."""
import ast
from pathlib import Path
import threading
import unittest

from serve import frontend, server
from serve.minimax import MiniMaxOutputParser, THINK, THINK_END
from serve.test_minimax_frontend import template, tokenizer

REASONING = 'The user greeted me in Russian. I should greet them back briefly.'
ANSWER = 'Привет! 👋 Как дела? Чем могу помочь?'
SCREENSHOT = THINK + REASONING + THINK_END + ANSWER


def startup_service(script, cfg=None, tok=None, eos=True):
    cfg = cfg or {'engine_kind': 'mm3', 'model_arch': 'minimax-m3'}
    tok = tok or tokenizer()
    engine = server.MockEngine(tok, script)
    engine.scripts = [tok.encode(script, parse_special=True) + ([tok.ids['[e~[']] if eos else [])]
    engine.script = engine.scripts[0]
    service = server.Service(engine, tok, template(), model_name='minimax-test')
    tree = ast.parse(Path(server.__file__).read_text(encoding='utf-8'))
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
    block = next(n for n in ast.walk(main) if isinstance(n, ast.If) and n.body and
                 isinstance(n.body[0], ast.Assign) and any(isinstance(t, ast.Attribute) and
                 isinstance(t.value, ast.Name) and t.value.id == 'svc' and t.attr == 'model_arch'
                 for t in n.body[0].targets))
    # Exactly the shipped assignment and set_family call: no network/native process/main invocation.
    scope = {'cfg': cfg, 'svc': service}
    exec(compile(ast.Module(body=block.body[:2], type_ignores=[]), str(Path(server.__file__)), 'exec'), scope)
    return service


def run_reply(service, prefix, maximum=512, thinking=True):
    ids = service.tok.encode(prefix, parse_special=True)
    output = list(service.run(ids, thinking, None, maximum, {}, threading.Event()))
    events = [v for k, v in output if k == 'event']
    return ({kind: ''.join(e.text for e in events if e.kind == kind) for kind in ['reasoning', 'content']},
            next(v for k, v in output if k == 'done'))


class MiniMaxStartupIdentity(unittest.TestCase):
    def tearDown(self):
        frontend.use_family(None)

    def test_main_uses_qualified_model_arch_not_qwen_default(self):
        service = startup_service('answer')
        self.assertEqual(service.model_arch, 'minimax-m3')
        self.assertEqual(service.family, 'minimax')
        self.assertIs(service.parser_cls, MiniMaxOutputParser)
        self.assertEqual(service.stop_ids, {service.tok.ids['[e~[']})

    def test_screenshot_adaptive_stream_has_real_final_answer(self):
        service = startup_service(SCREENSHOT)
        text, done = run_reply(service, ']~b]ai\n')
        self.assertEqual(text, {'reasoning': REASONING, 'content': ANSWER})
        self.assertEqual(done['finish'], 'stop')

    def test_enabled_native_prefill_closes_into_content(self):
        service = startup_service(REASONING + THINK_END + ANSWER)
        text, done = run_reply(service, ']~b]ai\n' + THINK)
        self.assertEqual(text, {'reasoning': REASONING, 'content': ANSWER})
        self.assertEqual(done['finish'], 'stop')

    def test_disabled_plain_answer_uses_content(self):
        service = startup_service(ANSWER)
        ids, thinking, _ = service.prepare([{'role': 'user', 'content': 'привет'}], None,
                                          {'enable_thinking': False}, 512)
        self.assertFalse(thinking)
        self.assertEqual(ids[-1], service.tok.ids[THINK_END])
        text, done = run_reply(service, service.tok.decode(ids), thinking=thinking)
        self.assertEqual(text, {'reasoning': '', 'content': ANSWER})
        self.assertEqual(done['finish'], 'stop')

    def test_unrequested_model_thinking_still_stays_private(self):
        service = startup_service(SCREENSHOT)
        text, _ = run_reply(service, ']~b]ai\n' + THINK_END, thinking=False)
        self.assertEqual(text, {'reasoning': REASONING, 'content': ANSWER})

    def test_natural_eos_and_length_cap_are_distinct_no_reasoning_fallback(self):
        for eos, cap, finish in [(True, 512, 'stop'), (False, 512, 'length'), (True, 12, 'length')]:
            with self.subTest(eos=eos, cap=cap):
                service = startup_service(SCREENSHOT, eos=eos)
                text, done = run_reply(service, ']~b]ai\n', maximum=cap)
                self.assertEqual(done['finish'], finish)
                if cap == 12:
                    self.assertEqual(text['content'], '')
                    self.assertNotIn(ANSWER, text['reasoning'])

    def test_native_marker_split_boundaries_after_startup_selection(self):
        service = startup_service(SCREENSHOT)
        schedules = [[SCREENSHOT], *[[SCREENSHOT[i:i+n] for i in range(0, len(SCREENSHOT), n)] for n in [1, 2, 7]]]
        schedules += [[SCREENSHOT[:i], SCREENSHOT[i:]] for i in range(1, len(SCREENSHOT))]
        for pieces in schedules:
            parser = service.parser_cls(thinking=False, declared_only=True)
            events = [event for piece in pieces for event in parser.feed(piece)] + parser.finish('stop')
            self.assertEqual(''.join(e.text for e in events if e.kind == 'reasoning'), REASONING)
            self.assertEqual(''.join(e.text for e in events if e.kind == 'content'), ANSWER)

    def test_non_mm3_arch_default_unchanged(self):
        for cfg, expected in [({'engine_kind': 'strata'}, 'qwen4exp'),
                              ({'engine_kind': 'strata', 'arch': 'qwen35moe', 'model_arch': 'minimax-m3'}, 'qwen35moe')]:
            with self.subTest(cfg=cfg):
                service = startup_service('answer', cfg=cfg)
                self.assertEqual(service.model_arch, expected)
                self.assertIs(service.parser_cls, server.OutputParser)


if __name__ == '__main__':
    unittest.main()
