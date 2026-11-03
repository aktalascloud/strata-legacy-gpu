"""Current request declarations remain authoritative even when old assistant turns name other tools.
MockEngine only: no HTTP listener, native engine, GPU or model request.
"""
import contextlib
import io
from pathlib import Path
import threading
import unittest

from serve.server import ByteTokenizer, MockEngine, Service
from serve.frontend import ChatTemplate, OutputParser

TODO = {"name": "TodoWrite", "parameters": {"type": "object", "properties": {"todos": {"type": "array"}}}}
BASH = {"name": "Bash", "parameters": {"type": "object", "properties": {"command": {"type": "string"}}}}
CALL = "<tool_call>\n<function=Bash>\n<parameter=command>\nls -la\n</parameter>\n</function>\n</tool_call>"


class HistoryTools(unittest.TestCase):
    def run_script(self, tools, history_name=None, req=None):
        tok = ByteTokenizer()
        template = ChatTemplate(Path(__file__).parent / "chat_template.jinja")
        svc = Service(MockEngine(tok, CALL, max_context=16384), tok, template)
        if req is None:
            req = {"messages": [{"role": "assistant", "tool_calls": [{"function": {"name": history_name}}]}]}
        with contextlib.redirect_stdout(io.StringIO()):
            rows = list(svc.run([], False, tools, 512, req, threading.Event(), declared_only=True))
        events = [value for kind, value in rows if kind == "event"]
        return [e.call for e in events if e.kind == "tool_call"], "".join(e.text for e in events if e.kind == "content")

    def test_old_tool_is_not_implicitly_declared(self):
        calls, answer = self.run_script([TODO], "Bash")
        self.assertEqual(calls, [])
        self.assertIn("<tool_call>", answer)

    def test_current_declaration_retains_its_schema(self):
        calls, answer = self.run_script([TODO, BASH], "Bash")
        self.assertEqual([(c.name, c.arguments) for c in calls], [("Bash", {"command": "ls -la"})])
        self.assertEqual(answer, "")

    def test_unrelated_history_does_not_change_current_tools(self):
        calls, _ = self.run_script([TODO], "Read")
        self.assertEqual(calls, [])

    def test_no_tools_does_not_gain_tools_from_history(self):
        calls, answer = self.run_script([], "Bash")
        self.assertEqual(calls, [])
        self.assertIn("<tool_call>", answer)

    def test_other_route_history_does_not_authorize_tools(self):
        requests = [
            {"messages": [{"role": "assistant", "content": [{"type": "tool_use", "name": "Bash", "id": "t1", "input": {}}]}]},
            {"input": [{"type": "function_call", "name": "Bash", "call_id": "c1", "arguments": "{}"}]},
            {"input": [{"type": "function_call", "namespace": "mcp", "name": "Bash", "call_id": "c1", "arguments": "{}"}]},
        ]
        for req in requests:
            with self.subTest(req=req):
                calls, answer = self.run_script([TODO], req=req)
                self.assertEqual(calls, [])
                self.assertIn("<tool_call>", answer)

    def test_deferred_flag_does_not_authorize_unknown_names(self):
        for tools, expected in (([TODO], []), ([TODO, BASH], ["Bash"])):
            with self.subTest(tools=tools):
                parser = OutputParser(thinking=False, tools=tools, deferred=True)
                events = parser.feed(CALL) + parser.finish("stop")
                self.assertEqual([e.call.name for e in events if e.kind == "tool_call"], expected)



class PrefixedNames(unittest.TestCase):
    """#4751: `tools.write` for a declared `write` (a programmatic-tool-calling harness shows the model `tools.write(...)`)."""

    WRITE = {"name": "write", "parameters": {"type": "object", "properties": {"file_path": {"type": "string"}, "content": {"type": "string"}}}}
    TEXT = ("<tool_call>\n<function=tools.write>\n<parameter=file_path>/a/b.py</parameter>\n"
            "<parameter=content>x = 1\n</parameter>\n</function>\n</tool_call>")

    def calls(self, tools, text=None):
        p = OutputParser(thinking=False, tools=tools, stream_tools=True, recover=True, declared_only=True)
        evs = p.feed(text or self.TEXT) + p.finish("stop")
        return [e.call for e in evs if e.kind == "tool_call"], "".join(e.text for e in evs if e.kind == "content")

    def test_the_prefix_is_read_as_the_declared_tool(self):
        calls, answer = self.calls([self.WRITE])
        self.assertEqual([(c.name, c.arguments["file_path"]) for c in calls], [("write", "/a/b.py")])
        self.assertEqual(answer, "")

    def test_functions_prefix_too(self):
        calls, _ = self.calls([self.WRITE], self.TEXT.replace("tools.write", "functions.write"))
        self.assertEqual([c.name for c in calls], ["write"])

    def test_an_undeclared_name_stays_text(self):
        calls, answer = self.calls([self.WRITE], self.TEXT.replace("tools.write", "tools.delete"))
        self.assertEqual(calls, [])
        self.assertIn("<tool_call>", answer)

    def test_a_declared_dotted_name_wins(self):
        dotted = {"name": "tools.write", "parameters": self.WRITE["parameters"]}
        calls, _ = self.calls([self.WRITE, dotted])
        self.assertEqual([c.name for c in calls], ["tools.write"])


if __name__ == "__main__":
    unittest.main()
