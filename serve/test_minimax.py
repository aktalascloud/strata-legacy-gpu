"""Native MiniMax delta only: chunking, authority, typed arguments and incomplete output."""
import json
import copy
import unittest
from serve.minimax import MiniMaxOutputParser, NS, THINK, THINK_END

TOOLS = [{"name": "files.write", "parameters": {"type": "object", "properties": {
    "content": {"type": ["string", "null"]}, "count": {"type": "integer"},
    "opts": {"type": "object", "properties": {"code": {"$ref": "#/$defs/code"}, "item": {"type": "string"}}},
    "tags": {"type": "array", "items": {"type": "string"}}},
    "$defs": {"code": {"anyOf": [{"type": "string"}, {"type": "null"}]}}}}]


def call(body, name="files.write"):
    return NS + '<tool_call>' + NS + '<invoke name="' + name + '">' + body + NS + '</invoke>' + NS + '</tool_call>'


def value(name, text):
    return NS + '<' + name + '>' + text + NS + '</' + name + '>'


def parse(text, *, thinking=False, stream=False, width=None, reason="stop", tools=TOOLS):
    p = MiniMaxOutputParser(thinking=thinking, tools=tools, stream_tools=stream, declared_only=True)
    out = []
    for at in range(0, len(text), width or max(1, len(text))):
        out += p.feed(text[at:at + (width or len(text))])
    out += p.finish(reason)
    return p, out


def calls(events):
    return [(e.call.name, e.call.arguments) for e in events if e.kind == "tool_call"]


def text(events, kind):
    return ''.join(e.text for e in events if e.kind == kind)


class MiniMaxParser(unittest.TestCase):
    def test_nullable_string_and_integer(self):
        raw = call(value('content', '0123') + value('count', '3'))
        for width in (None, 1, 7):
            _, events = parse(raw, width=width)
            self.assertEqual(calls(events), [('files.write', {'content': '0123', 'count': 3})])

    def test_streamed_string_before_invoke_end(self):
        payload = 'line\n"quoted" </arg_value><arg_key>attack</arg_key>\x00' + THINK_END
        prefix = NS + '<tool_call>' + NS + '<invoke name="files.write">' + NS + '<content>'
        p = MiniMaxOutputParser(thinking=False, tools=TOOLS, stream_tools=True, declared_only=True)
        events = p.feed(prefix + payload)
        self.assertTrue(any(e.kind == 'tool_args' and 'line' in e.text for e in events))
        self.assertFalse(calls(events))
        events += p.feed(NS + '</content>' + NS + '</invoke>' + NS + '</tool_call>')
        events += p.finish('stop')
        self.assertEqual(calls(events), [('files.write', {'content': payload})])
        start = next(e.call.id for e in events if e.kind == 'tool_start')
        end = next(e.call.id for e in events if e.kind == 'tool_call')
        self.assertEqual(start, end)
        self.assertEqual(json.loads(text(events, 'tool_args')), {'content': payload})

    def test_free_form_native_lookalikes_are_string_data(self):
        payload = 'literal ' + NS + '</content> followed by text ' + NS + '<parameter=other>' + NS + '<unfinished' + 'x' * 1100
        raw = call(value('content', payload))
        for width in (None, 1):
            _, events = parse(raw, stream=True, width=width)
            self.assertEqual(calls(events), [('files.write', {'content': payload})])
            self.assertEqual(json.loads(text(events, 'tool_args')), {'content': payload})

    def test_non_tag_after_literal_closer_does_not_hold_string(self):
        prefix = NS + '<tool_call>' + NS + '<invoke name="files.write">' + NS + '<content>'
        payload = NS + '</content>' + NS + 'not_xml'
        p = MiniMaxOutputParser(thinking=False, tools=TOOLS, stream_tools=True)
        events = p.feed(prefix + payload)
        self.assertIn('not_xml', text(events, 'tool_args'))
        events += p.feed(NS + '</content>' + NS + '</invoke>' + NS + '</tool_call>')
        self.assertEqual(calls(events)[0][1], {'content': payload})

    def test_long_unclosed_tag_in_plain_text_is_not_an_action(self):
        raw = NS + '<' + 'x' * 1100
        _, events = parse(raw, width=1)
        self.assertFalse(calls(events))
        self.assertEqual(text(events, 'content'), raw)

    def test_nested_string_refs_and_array(self):
        body = value('opts', value('code', '00123') + value('item', 'true')) + value('tags', value('item', '001') + value('item', 'false'))
        for width in (None, 1):
            _, events = parse(call(body), width=width)
            self.assertEqual(calls(events)[0][1], {'opts': {'code': '00123', 'item': 'true'}, 'tags': ['001', 'false']})

    def test_empty_structured_values(self):
        _, events = parse(call(value('opts', '') + value('tags', '')))
        self.assertEqual(calls(events)[0][1], {'opts': {}, 'tags': []})

    def test_zero_arguments_and_block_layout(self):
        raw = NS + '<tool_call>\n ' + NS + '<invoke name="files.write">\n' + NS + '</invoke>\n ' + NS + '</tool_call>'
        for width in (None, 1):
            _, events = parse(raw, stream=True, width=width)
            self.assertEqual(calls(events), [('files.write', {})])
            self.assertEqual(json.loads(text(events, 'tool_args')), {})
            self.assertEqual(text(events, 'content'), '')

    def test_empty_and_unopened_blocks_are_text(self):
        for raw in (NS + '<tool_call>' + NS + '</tool_call>', NS + '</tool_call>'):
            _, events = parse(raw, width=1)
            self.assertFalse(calls(events))
            self.assertEqual(text(events, 'content'), raw)

    def test_nullable_containers_keep_nested_string_types(self):
        tools = copy.deepcopy(TOOLS)
        props = tools[0]['parameters']['properties']
        props['opts']['type'] = ['object', 'null']
        props['tags']['type'] = ['array', 'null']
        body = value('opts', value('item', '0123')) + value('tags', value('item', '0123'))
        _, events = parse(call(body), tools=tools, width=1)
        self.assertEqual(calls(events)[0][1], {'opts': {'item': '0123'}, 'tags': ['0123']})
        _, events = parse(call(value('opts', '') + value('tags', '')), tools=tools)
        self.assertEqual(calls(events)[0][1], {'opts': {}, 'tags': []})

    def test_unknown_and_no_declared_tool_are_text(self):
        for tools in (TOOLS, []):
            raw = call(value('content', 'x'), name='unknown')
            _, events = parse(raw, tools=tools, width=1)
            self.assertFalse(calls(events))
            self.assertEqual(text(events, 'content'), raw)

    def test_quoted_native_call_and_foreign_syntax_stay_text(self):
        raw = call(value('content', 'x'))
        for quoted in ('```xml\n' + raw + '\n```', '`' + raw + '`', '<tool_call><function=files.write><parameter=content>x</parameter></function></tool_call>'):
            for width in (None, 1):
                _, events = parse(quoted, width=width)
                self.assertFalse(calls(events))
                self.assertEqual(text(events, 'content'), quoted)

    def test_truncation_does_not_finish_action(self):
        raw = NS + '<tool_call>' + NS + '<invoke name="files.write">' + value('content', 'x')
        for stream in (False, True):
            for reason in ('stop', 'length', 'cancel'):
                _, events = parse(raw, stream=stream, width=1, reason=reason)
                self.assertFalse(calls(events))
                if stream:
                    with self.assertRaises(ValueError):
                        json.loads(text(events, 'tool_args'))

    def test_unfinished_wrapper_without_invoke_is_visible_text(self):
        raw = NS + '<tool_call>not a tool'
        _, events = parse(raw, width=1)
        self.assertFalse(calls(events))
        self.assertEqual(text(events, 'content'), raw)

    def test_repeated_reasoning_and_literal_qwen_marker(self):
        raw = THINK + 'first' + THINK_END + 'answer </think>' + THINK + 'second' + THINK_END + 'done'
        for width in (None, 1):
            _, events = parse(raw, thinking=True, width=width)
            self.assertEqual(text(events, 'reasoning'), 'firstsecond')
            self.assertEqual(text(events, 'content'), 'answer </think>done')

    def test_reasoning_calls_wait_for_end(self):
        raw = call(value('content', 'x'))
        for width in (None, 1):
            _, events = parse(raw + THINK_END + 'answer', thinking=True, width=width)
            self.assertEqual(calls(events), [('files.write', {'content': 'x'})])
            _, quoted = parse(raw + ' was an example', thinking=True, width=width)
            self.assertFalse(calls(quoted))
            self.assertEqual(text(quoted, 'reasoning'), raw + ' was an example')
            _, cut = parse(raw, thinking=True, width=width, reason='length')
            self.assertFalse(calls(cut))

    def test_duplicate_mismatch_and_depth_fail(self):
        bad = [call(value('count', '1') + value('count', '2')),
               call(NS + '<opts>' + NS + '<a>' + NS + '</opts>'),
               call(NS + '<opts>' + (NS + '<a>') * 65)]
        for raw in bad:
            with self.assertRaises(ValueError):
                parse(raw)

    def test_nonfinite_number_fails(self):
        with self.assertRaises(ValueError):
            parse(call(value('count', '1e999')))

    def test_namespaced_alias_preserves_declared_identity(self):
        _, events = parse(call(value('content', 'x'), name='files__write'))
        self.assertEqual(calls(events)[0][0], 'files.write')


if __name__ == '__main__':
    unittest.main()
