"""MiniMax frontend wiring, offline templates and scripted service; no model or GPU."""
import hashlib
import threading
import unittest
from pathlib import Path
from serve import frontend as f
from serve.minimax import LEVELS, NS, THINK, THINK_END, MiniMaxOutputParser, to_minimax_force
from serve.server import MockEngine, Service
from tools.strata_tokenizer import BYTE_TO_UNICODE
from serve.minimax_tokenizer import Tokenizer

FIXTURE = Path(__file__).parent / 'fixtures/minimax_m31'
TOOLS = [{'name': 'files.write', 'parameters': {'type': 'object', 'properties': {'content': {'type': 'string'}}}}]


def template(official=False):
    t = f.ChatTemplate(FIXTURE / ('official_chat_template.jinja' if official else 'chat_template.jinja'))
    t.tool_style = 'openai'
    if not official:
        t.model_family = 'minimax'
    return t


def tokenizer():
    specials = [']~b]', '[e~[', THINK, THINK_END, NS, ']!p~[', ']~!b[']
    return Tokenizer([BYTE_TO_UNICODE[i] for i in range(256)] + specials, [], [1] * 256 + [3] * len(specials), pre='minimax')


def service(script):
    tok = tokenizer()
    engine = MockEngine(tok, script)
    # Production MockEngine's end marker is Qwen's. This fixture replays MiniMax's own EOS.
    engine.scripts = [tok.encode(s, parse_special=True) + [tok.ids['[e~[']] for s in ([script] if isinstance(script, str) else script)]
    engine.script = engine.scripts[0]
    s = Service(engine, tok, template(), model_name='minimax-m3.1-flash')
    s.model_arch = 'minimax-m3'
    s.set_family(None)
    return s


class MiniMaxFrontend(unittest.TestCase):
    def tearDown(self):
        f.use_family(None)

    def test_own_levels_and_qwen_unchanged(self):
        f.use_family('minimax')
        for level in LEVELS:
            self.assertEqual(f.effort_kwargs(level), {'reasoning_effort': level})
        self.assertEqual(f.effort_kwargs(False), {'enable_thinking': False})
        f.use_family(None)
        self.assertEqual(f.effort_kwargs('high'), {'reasoning_effort': 'xhigh'})
        self.assertEqual(f.effort_kwargs('max'), {'reasoning_effort': 'xhigh'})

    def test_original_default_template_bytes(self):
        original = FIXTURE / 'official_chat_template.jinja'
        self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(), '961e3f96b2c08d26555efdfeb3b384d5e81181bf0cfc04edbadc31c6e507b431')
        messages = [{'role': 'system', 'content': 'Be brief.'}, {'role': 'user', 'content': 'Hello.'}]
        original_renderer = template(True).template
        for tools in (None, TOOLS):
            wrapped = [{'type': 'function', 'function': t} for t in tools] if tools else None
            expected = original_renderer.render(messages=messages, tools=wrapped, add_generation_prompt=True)
            self.assertEqual(template().render(messages, tools=tools), expected)

    def test_named_levels_and_native_off(self):
        t = template();messages = [{'role': 'user', 'content': 'Hello.'}]
        for level in LEVELS:
            self.assertIn('<effort>' + level + '</effort>', t.render(messages, reasoning_effort=level))
        off = t.render(messages, enable_thinking=False, reasoning_effort='max')
        self.assertIn('Current thinking mode: disabled.', off)
        self.assertTrue(off.endswith(THINK_END))
        self.assertNotIn('<effort>max</effort>', off)
        with self.assertRaises(ValueError):
            t.render(messages, author_mode='Adaptive')

    def test_forced_tool_prefixes(self):
        self.assertIsNone(to_minimax_force(None))
        self.assertEqual(to_minimax_force('<tool_call>\n'), NS + '<tool_call>')
        named = to_minimax_force(f.forced_call({'type': 'function', 'function': {'name': 'files.write'}}, TOOLS))
        self.assertEqual(named, NS + '<tool_call>' + NS + '<invoke name="files.write">')
        p = MiniMaxOutputParser(thinking=False, tools=TOOLS)
        ev = p.feed(named) + p.feed(NS + '<content>x' + NS + '</content>' + NS + '</invoke>' + NS + '</tool_call>') + p.finish('stop')
        self.assertEqual([e.call.arguments for e in ev if e.kind == 'tool_call'], [{'content': 'x'}])

    def test_family_requires_metadata_not_display_name(self):
        s = service('answer')
        self.assertEqual(s.family, 'minimax')
        self.assertIs(s.parser_cls, MiniMaxOutputParser)
        self.assertEqual(s.stop_ids, {s.tok.ids['[e~[']})
        s.family = None;s.tok.pre = 'qwen35'
        with self.assertRaises(ValueError):
            s.set_family('minimax')
        self.assertIsNone(s.family)

    def test_adaptive_plain_answer_and_prefilled_thinking(self):
        s = service('plain answer')
        ids = s.tok.encode(']~b]ai\n', parse_special=True)
        out = list(s.run(ids, True, None, 128, {}, threading.Event()))
        ev = [v for k, v in out if k == 'event']
        self.assertEqual(''.join(e.text for e in ev if e.kind == 'content'), 'plain answer')
        self.assertFalse(any(e.kind == 'reasoning' for e in ev))
        s = service('thought' + THINK_END + 'answer')
        ids = s.tok.encode(']~b]ai\n' + THINK, parse_special=True)
        out = list(s.run(ids, True, None, 128, {}, threading.Event()))
        ev = [v for k, v in out if k == 'event']
        self.assertEqual(''.join(e.text for e in ev if e.kind == 'reasoning'), 'thought')
        self.assertEqual(''.join(e.text for e in ev if e.kind == 'content'), 'answer')

    def test_prepare_native_prefix_and_disabled_force(self):
        messages = [{'role': 'user', 'content': 'Hello.'}]
        s = service('answer')
        ids, thinking, _ = s.prepare(messages, None, {'thinking_mode': 'enabled'}, 128)
        self.assertTrue(thinking)
        self.assertEqual(ids[-1], s.tok.ids[THINK])
        force = to_minimax_force(f.forced_call({'type': 'function', 'function': {'name': 'files.write'}}, TOOLS))
        ids, thinking, _ = s.prepare(messages, TOOLS, {'thinking_mode': 'disabled'}, 128, force=force)
        self.assertFalse(thinking)
        self.assertTrue(s.tok.decode(ids).endswith(force))

    def test_budget_wrap_uses_native_end_marker(self):
        s = service(['long reasoning text', 'answer'])
        original = s.engine.generate
        prompts = []
        def capture(ids, *args):
            prompts.append(list(ids))
            yield from original(ids, *args)
        s.engine.generate = capture
        ids = s.tok.encode(']~b]ai\n' + THINK, parse_special=True)
        out = list(s.run(ids, True, None, 256, {'reasoning_budget_tokens': 2}, threading.Event()))
        self.assertEqual(len(prompts), 2)
        self.assertIn(THINK_END, s.tok.decode(prompts[1]))
        self.assertNotIn('</think>', s.tok.decode(prompts[1]))
        ev = [v for k, v in out if k == 'event']
        self.assertEqual(''.join(e.text for e in ev if e.kind == 'content').strip(), 'answer')


if __name__ == '__main__':
    unittest.main()
