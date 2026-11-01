"""Current request declarations remain authoritative even when old assistant turns name other tools.
MockEngine only: no HTTP listener, native engine, GPU or model request.
"""
import contextlib
import io
from pathlib import Path
import threading
import unittest

from serve.server import ByteTokenizer, MockEngine, Service
from serve.frontend import ChatTemplate

TODO = {"name": "TodoWrite", "parameters": {"type": "object", "properties": {"todos": {"type": "array"}}}}
BASH = {"name": "Bash", "parameters": {"type": "object", "properties": {"command": {"type": "string"}}}}
CALL = "<tool_call>\n<function=Bash>\n<parameter=command>\nls -la\n</parameter>\n</function>\n</tool_call>"


class HistoryTools(unittest.TestCase):
    def run_script(self, tools, history_name):
        tok = ByteTokenizer()
        template = ChatTemplate(Path(__file__).parent / "chat_template.jinja")
        svc = Service(MockEngine(tok, CALL, max_context=16384), tok, template)
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


if __name__ == "__main__":
    unittest.main()
