"""PR4835 Responses force regression cases; upstream MIT, no model/GPU."""
import contextlib
import http.client
import io
import json
import unittest
from serve import responses
from serve.server import MockEngine
from serve.test_responses import Server, TOOLS

class ForcingEngine(MockEngine):
    """Thinks, then answers in text - unless its prompt already opens a call (a forced tool_choice): then it finishes
    that call.  Records every prompt it is given."""
    THOUGHT = "I could look this up. "
    ANSWER = "The answer is 4."
    ARGS = "<parameter=cmd>\nls\n</parameter>\n</function>\n</tool_call>"
    first_name = "exec_command"                      # what the model writes after a bare "<tool_call>\n"

    def __init__(self, tok):
        super().__init__(tok, "x", max_context=16384)
        self.prompts = []

    def generate(self, ids, max_new, sampling, cancel, embeddings=None):
        self.prompts.append(list(ids))
        prompt = self.tok.decode(ids)
        if prompt.endswith("<tool_call>\n"):
            text = "<function=" + self.first_name + ">\n" + self.ARGS
        elif prompt.endswith(("<function=exec_command>\n", "<function=apply_patch>\n", "<function=mcp__fs.read>\n")):
            text = self.ARGS
        elif prompt.endswith("</think>\n\n"):
            text = self.ANSWER
        else:
            text = self.THOUGHT + "</think>\n\n" + self.ANSWER
        for t in (self.tok.encode(text) + self.tok.encode("<|im_end|>", parse_special=True))[:max_new]:
            if cancel.is_set():
                return
            yield t


class ForcedToolChoice(Server):
    def post(self, body, path="/v1/responses", headers=None, log=None):
        """(status, parsed body: a dict, or the list of SSE events of a stream).  `log` gets what the server prints."""
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
        try:
            with contextlib.redirect_stdout(log or io.StringIO()):
                c.request("POST", path, body=json.dumps(body).encode(),
                          headers={"Content-Type": "application/json", **(headers or {})})
                r = c.getresponse()
                raw = r.read().decode()
            if r.getheader("Content-Type") == "text/event-stream":
                events = []
                for block in raw.split("\n\n"):
                    lines = block.strip().splitlines()
                    if not lines or lines[0].startswith(":"):
                        continue
                    name = lines[0][len("event: "):]
                    data = json.loads(lines[1][len("data: "):])
                    self.assertEqual(name, data["type"])
                    events.append(data)
                return r.status, events
            return r.status, json.loads(raw)
        finally:
            c.close()

    """#790's follow-up: tool_choice "required" or a named function opens the call here too, as on the chat route."""
    TWO = TOOLS + [{"type": "function", "name": "other", "parameters": {"type": "object", "properties": {}}}]
    NAMED = {"type": "function", "name": "exec_command"}
    NO_THINKING = {"reasoning": {"effort": "none"}}

    def setUp(self):
        super().setUp()
        self.engine = self.svc.engine = ForcingEngine(self.tok)

    def request(self, **extra):
        return {"model": "m", "input": "hi", "tools": self.TWO, **extra}

    def final(self, body):
        """The finished response of a whole reply or of a stream."""
        code, r = self.post(body)
        self.assertEqual(code, 200, r)
        return r[-1]["response"] if body.get("stream") else r

    def test_required_and_named_after_the_thinking(self):
        for choice in ("required", self.NAMED):
            for stream in (False, True):
                with self.subTest(choice=choice, stream=stream):
                    self.engine.prompts = []
                    r = self.final(self.request(tool_choice=choice, stream=stream))
                    self.assertEqual(r["status"], "completed")
                    self.assertEqual([o["type"] for o in r["output"]], ["reasoning", "function_call"])
                    call = r["output"][-1]
                    self.assertEqual((call["name"], json.loads(call["arguments"])), ("exec_command", {"cmd": "ls"}))
                    self.assertEqual(r["tool_choice"], choice)
                    self.assertEqual(len(self.engine.prompts), 2, "the thinking, then the call")
                    first, second = self.engine.prompts
                    opening = "<tool_call>\n" + ("<function=exec_command>\n" if choice == self.NAMED else "")
                    self.assertEqual(second, first + self.tok.encode(ForcingEngine.THOUGHT + "</think>\n\n" + opening))

    def test_without_thinking_the_prompt_ends_with_the_opening(self):
        for choice in ("required", self.NAMED):
            for stream in (False, True):
                with self.subTest(choice=choice, stream=stream):
                    self.engine.prompts = []
                    r = self.final(self.request(tool_choice=choice, stream=stream, **self.NO_THINKING))
                    self.assertEqual([o["type"] for o in r["output"]], ["function_call"])
                    self.assertEqual(r["output"][0]["name"], "exec_command")
                    self.assertEqual(len(self.engine.prompts), 1)
                    opening = "<tool_call>\n" + ("<function=exec_command>\n" if choice == self.NAMED else "")
                    self.assertTrue(self.tok.decode(self.engine.prompts[0]).endswith("</think>\n\n" + opening))

    def test_the_stream_sends_the_call_as_its_events(self):
        code, events = self.post(self.request(tool_choice="required", stream=True, **self.NO_THINKING))
        self.assertEqual(code, 200)
        kinds = [e["type"] for e in events]
        self.assertIn("response.function_call_arguments.done", kinds)
        self.assertNotIn("response.output_text.delta", kinds)

    def test_required_lets_the_model_pick_among_the_tools(self):
        self.engine.first_name = "other"
        self.engine.ARGS = "</function>\n</tool_call>"
        r = self.final(self.request(tool_choice="required", **self.NO_THINKING))
        self.assertEqual([(o["type"], o.get("name")) for o in r["output"]], [("function_call", "other")])

    def test_a_custom_tool_and_a_namespaced_tool(self):
        self.engine.ARGS = "<parameter=input>\nx\n</parameter>\n</function>\n</tool_call>"
        self.engine.first_name = "apply_patch"
        r = self.final(self.request(tools=[{"type": "custom", "name": "apply_patch"}], tool_choice="required",
                                    **self.NO_THINKING))
        self.assertEqual([(o["type"], o.get("name"), o.get("input")) for o in r["output"]],
                         [("custom_tool_call", "apply_patch", "x")])
        self.engine.ARGS = "</function>\n</tool_call>"
        space = [{"type": "namespace", "name": "mcp__fs", "tools": [{"type": "function", "name": "read"}]}]
        r = self.final(self.request(tools=space, tool_choice={"type": "function", "name": "mcp__fs.read"},
                                    **self.NO_THINKING))
        self.assertEqual([(o["type"], o.get("namespace"), o.get("name")) for o in r["output"]],
                         [("function_call", "mcp__fs", "read")])

    def test_a_format_binds_the_answer_not_the_forced_call(self):
        r = self.final(self.request(tool_choice="required", text={"format": {"type": "json_object"}},
                                    **self.NO_THINKING))
        self.assertEqual([o["type"] for o in r["output"]], ["function_call"])

    def test_the_other_spellings_force_too(self):
        """tool_choice_of reads the chat route's and the Anthropic route's shapes as well."""
        for choice, opening in (({"type": "function", "function": {"name": "exec_command"}}, "<function=exec_command>\n"),
                                ({"type": "tool", "name": "exec_command"}, "<function=exec_command>\n"),
                                ({"type": "any"}, ""), ({"type": "required"}, "")):
            with self.subTest(choice=choice):
                self.engine.prompts = []
                r = self.final(self.request(tool_choice=choice, **self.NO_THINKING))
                self.assertEqual([o["type"] for o in r["output"]], ["function_call"])
                self.assertTrue(self.tok.decode(self.engine.prompts[0]).endswith("<tool_call>\n" + opening))

    def test_what_the_force_does_not_catch(self):
        """No grammar: the opening is all the server writes.  These replies are not a good call, and say so here."""
        self.engine.ARGS = "Sorry, I cannot."
        fmt = {"text": {"format": {"type": "json_object"}}}
        for extra in ({}, fmt):                      # a named call opened: the text is dropped, the call is unfinished
            with self.subTest(named=extra):
                r = self.final(self.request(tool_choice=self.NAMED, **extra, **self.NO_THINKING))
                self.assertEqual(r["status"], "completed")
                self.assertEqual([(o["type"], o["status"], o.get("arguments")) for o in r["output"]],
                                 [("function_call", "incomplete", "{")])
        self.engine.first_name = "nosuch"            # "required": a name that is no tool is text, which a format refuses
        r = self.final(self.request(tool_choice="required", **self.NO_THINKING))
        self.assertEqual([o["type"] for o in r["output"]], ["message"])
        code, r = self.post(self.request(tool_choice="required", **fmt, **self.NO_THINKING))
        self.assertEqual((code, r["error"]["code"]), (502, "structured_output_failed"))
        self.svc.engine = MockEngine(self.tok, "Still thinking", max_context=16384)   # the reply ends inside the thinking
        r = self.final(self.request(tool_choice=self.NAMED))
        self.assertEqual([o["type"] for o in r["output"]], ["reasoning"])

    def test_a_name_the_request_never_offered_stays_text(self):
        self.engine.first_name = "nosuch"
        r = self.final(self.request(tool_choice="required", **self.NO_THINKING))
        self.assertEqual([o["type"] for o in r["output"]], ["message"])
        self.assertIn("<function=nosuch>", r["output"][0]["content"][0]["text"])

    def test_auto_absent_and_none_leave_the_tools_to_the_model(self):
        for extra in ({}, {"tool_choice": "auto"}, {"tool_choice": "none"}):
            with self.subTest(extra=extra):
                self.engine.prompts = []
                log = io.StringIO()
                code, r = self.post(self.request(**extra), log=log)
                self.assertEqual(code, 200, r)
                self.assertNotIn("[strata] tool_choice", log.getvalue())
                self.assertEqual([o["type"] for o in r["output"]], ["reasoning", "message"])
                self.assertEqual(r["output"][-1]["content"][0]["text"], ForcingEngine.ANSWER)
                self.assertEqual(len(self.engine.prompts), 1)

    def test_a_choice_it_cannot_honour_acts_as_auto(self):
        """forced_call's rule: an odd choice is logged and must not stop the request."""
        allowed = {"type": "allowed_tools", "mode": "required", "tools": [{"type": "function", "name": "other"}]}
        space = [{"type": "namespace", "name": "mcp__fs", "tools": [{"type": "function", "name": "read"}]}]
        for extra in ({"tool_choice": {"type": "function", "name": "nosuch"}}, {"tool_choice": {"type": "web_search"}},
                      {"tool_choice": "sometimes"}, {"tool_choice": allowed},
                      {"tool_choice": {"type": "custom", "name": "other"}},
                      {"tool_choice": {"type": "function", "name": "read"}, "tools": space},
                      {"tool_choice": "required", "tools": []},
                      {"tool_choice": "required", "tools": [{"type": "web_search"}]}):
            with self.subTest(extra=extra):
                log = io.StringIO()
                code, r = self.post(self.request(**{**extra, **self.NO_THINKING}), log=log)
                self.assertEqual(code, 200, r)
                self.assertEqual([o["type"] for o in r["output"]], ["message"])
                self.assertEqual(log.getvalue().count("[strata] tool_choice"), 1, log.getvalue())

    def test_a_too_long_compaction_prompt_keeps_the_force_on_its_second_try(self):
        """The fallback of #924 renders the request again: the opening must be in that prompt too."""
        self.svc.codex_compaction_cache = True
        calls, prepare = [], self.svc.prepare

        def too_long_once(*args, **kw):
            calls.append(kw.get("force"))
            if len(calls) == 1:
                raise ValueError("too long for the context")
            return prepare(*args, **kw)
        self.svc.prepare = too_long_once
        shown = responses.prompt_tools
        responses.prompt_tools = lambda req, tools: list(tools)      # a list of its own: not the request's
        self.addCleanup(setattr, responses, "prompt_tools", shown)
        r = self.final(self.request(tool_choice=self.NAMED, **self.NO_THINKING))
        self.assertEqual(calls, ["<tool_call>\n<function=exec_command>\n"] * 2)
        self.assertEqual([o["type"] for o in r["output"]], ["function_call"])
