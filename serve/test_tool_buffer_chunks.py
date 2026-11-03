"""Large canonical string values retain structural context after compaction."""
import json
import unittest
from serve.frontend import OutputParser

TOOLS = [{'name': 'write', 'parameters': {'properties': {'content': {'type': 'string'}}}}]
OPEN = '<tool_call><function=write><parameter=content>\n'
CLOSE = '\n</parameter></function></tool_call>'


class ToolBufferChunks(unittest.TestCase):
    def test_large_value_quoted_tags_and_split_boundaries(self):
        for value in ('x' * 10000, 'x' * 5000 + ' literal </parameter> and </function> and </tool_call> ' + 'y' * 5000,
                      'x' * 5000 + ' "</parameter>" ' + 'y' * 5000,
                      'x' * 5000 + ' <tool_call><function=example><parameter=a>\nhi\n</parameter></function></tool_call> ' + 'y' * 5000):
            for step in (1, 7, 4096):
                with self.subTest(value=value[4998:5070], step=step):
                    p = OutputParser(thinking=False, tools=TOOLS, stream_tools=True, recover=True)
                    text = OPEN + value + CLOSE
                    events, peak = [], 0
                    for i in range(0, len(text), step):
                        events += p.feed(text[i:i + step])
                        if i + step <= len(OPEN) + len(value):
                            peak = max(peak, len(p.buf))
                    events += p.finish()
                    calls = [e.call for e in events if e.kind == 'tool_call']
                    self.assertEqual([(c.name, c.arguments) for c in calls], [('write', {'content': value})])
                    self.assertEqual(json.loads(''.join(e.text for e in events if e.kind == 'tool_args')), {'content': value})
                    if value == 'x' * 10000:
                        self.assertLess(peak, 8192)

    def test_bare_function_close_waits_for_wrapper_or_following_text(self):
        for ending in (' tail', '</tool_call> tail', ''):
            p = OutputParser(thinking=False, tools=TOOLS, stream_tools=True, recover=True)
            events = p.feed(OPEN[len('<tool_call>'):] + 'x' * 9000)
            self.assertFalse(p.clean)
            events += p.feed('\n</parameter></function>')
            events += p.feed(ending)
            events += p.finish()
            self.assertEqual([e.call.arguments for e in events if e.kind == 'tool_call'], [{'content': 'x' * 9000}])

    def test_truncated_call_restores_held_text_without_completed_tool(self):
        p = OutputParser(thinking=False, tools=TOOLS, stream_tools=True)
        events = p.feed(OPEN + 'x' * 9000)
        self.assertTrue(p._scan_parts)
        self.assertFalse(p.clean)
        events += p.finish('length')
        self.assertFalse(any(e.kind == 'tool_call' for e in events))


if __name__ == '__main__': unittest.main()
