"""PR4755/4756 JSON root and chat-tool regression cases; no GPU/model."""
import json
import unittest
from unittest import mock
from serve import structured
from serve.test_structured import Structured, STORY, FORMAT, HAVE_JSONSCHEMA

EXEC = [{"type":"function","function":{"name":"exec_command","parameters":{"type":"object","properties":{"cmd":{"type":"string"}},"required":["cmd"]}}}]

class ArraysAndTools(unittest.TestCase):
    setUp=Structured.setUp
    tearDown=Structured.tearDown
    request=Structured.request
    chat=Structured.chat

    def test_array_root_must_not_become_a_successful_object(self):
        fmt = {"type": "json_object"}
        cases = (
            '[{"answer":1}]',
            '[{"answer":1},{"answer":2}]',
            '[[{"answer":1}]]',
            '[[], [{"answer":1}]]',
            '[null, {"answer":1}]',
            '[false, {"answer":1}]',
            '[1, {"answer":1}]',
            '["a", {"answer":1}]',
            '[{"answer":1},]',
            'Here is the result: [{"answer":1},{"answer":2}]',
            '```json\n[{"answer":1}]\n```',
            '[{"answer":1}, BROKEN]',
            '[{"answer":1}',
            json.dumps(['text with ] and " escaped', {"answer": 1}]),
        )
        for script in cases:
            with self.subTest(script=script):
                code, reply = self.chat(script, response_format=fmt)
                self.assertEqual(code, 502)
                self.assertEqual(reply["error"]["code"], "structured_output_failed")
        for script in (cases[0], cases[1], cases[5]):
            with self.subTest(stream_script=script):
                code, raw = self.chat(script, response_format=fmt, stream=True)
                self.assertEqual(code, 200)
                self.assertIn('"structured_output_failed"', raw)
                self.assertNotIn('"delta"', raw)
                self.assertIn("data: [DONE]", raw)
        code, reply = self.chat('[' + json.dumps(STORY) + ']', response_format=FORMAT)
        self.assertEqual(code, 502)
        self.assertEqual(reply["error"]["code"], "structured_output_failed")
        with mock.patch.object(structured, "_jsonschema", False):
            code, reply = self.chat('[' + json.dumps(STORY) + ']', response_format=FORMAT)
            self.assertEqual(code, 502)
            self.assertEqual(reply["error"]["code"], "structured_output_failed")


    def test_prose_brackets_do_not_block_object_extraction(self):
        fmt = {"type": "json_object"}
        for script in (
            '[note] Result: {"answer":1}',
            '[one] [two] {"answer":1}',
            '[1 reason: {"answer":1}',
            'Context [2026 update: {"answer":1}',
            'Example [- this note {"answer":1}',
            'Quoted ["unfinished {"answer":1}',
            'Example [true story: {"answer":1}',
            'A long note [ 2 versions: {"answer":1}',
            'Draft [unfinished note. Result: {"answer":1}',
            'The character "[" is part of the explanation. {"answer":1}',
            '{"answer":1,"list":[{"n":2}]}',
        ):
            with self.subTest(script=script):
                code, reply = self.chat(script, response_format=fmt)
                self.assertEqual(code, 200)
                if '"list"' in script:
                    self.assertEqual(json.loads(reply["choices"][0]["message"]["content"]),
                                     {"answer": 1, "list": [{"n": 2}]})
                else:
                    self.assertEqual(reply["choices"][0]["message"]["content"], '{"answer":1}')


    def test_a_tool_call_passes_through_with_a_format(self):
        call = ("Let me look.\n</think>\n\nChecking.\n\n<tool_call>\n<function=exec_command>\n<parameter=cmd>\n"
                "cat a.txt\n</parameter>\n</function>\n</tool_call>")
        for stream in (False, True):
            with self.subTest(stream=stream):
                code, reply = self.chat(call, tools=EXEC, stream=stream)
                self.assertEqual(code, 200, reply)
                if stream:
                    chunks = [json.loads(line[6:]) for line in reply.splitlines() if line.startswith("data: {")]
                    calls = [tc for c in chunks for tc in c["choices"][0]["delta"].get("tool_calls") or []]
                    self.assertEqual(calls[0]["function"]["name"], "exec_command")
                    self.assertEqual(chunks[-1]["choices"][0]["finish_reason"], "tool_calls")
                else:
                    message = reply["choices"][0]["message"]
                    self.assertEqual(reply["choices"][0]["finish_reason"], "tool_calls")
                    self.assertEqual(json.loads(message["tool_calls"][0]["function"]["arguments"]), {"cmd": "cat a.txt"})
        self.assertIn("applies only to your final answer", self.tok.decode(self.engine.last_prompt))


    def test_the_final_answer_with_tools_is_the_schema_object(self):
        code, reply = self.chat(tools=EXEC)
        self.assertEqual(code, 200, reply)
        self.assertEqual(json.loads(reply["choices"][0]["message"]["content"]), STORY)
        code, raw = self.chat(tools=EXEC, stream=True)
        chunks = [json.loads(line[6:]) for line in raw.splitlines() if line.startswith("data: {")]
        self.assertEqual(json.loads("".join(c["choices"][0]["delta"].get("content", "") for c in chunks)), STORY)


    @unittest.skipUnless(HAVE_JSONSCHEMA, "jsonschema is not installed")
    def test_a_final_answer_with_tools_that_breaks_the_schema_fails(self):
        code, reply = self.chat('{"title":"Only a title"}', tools=EXEC)
        self.assertEqual((code, reply["error"]["code"]), (502, "structured_output_failed"))
