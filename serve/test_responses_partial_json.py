"""PR4830 length/JSON regression cases; no model or GPU."""
from serve.test_responses import Server

class PartialJson(Server):
    def say(self, text):
        self.engine.scripts = [self.tok.encode(text + "<|im_end|>", parse_special=True)]
        self.engine.script = self.engine.scripts[0]


    def test_json_format_cut_by_the_cap_ends_incomplete(self):
        answer = "{\"a\": \"bcdefghijklmnopqrstuvwxyz\"}"
        self.say(answer)
        ask = {"model": "m", "input": "json", "reasoning": {"effort": "none"}, "max_output_tokens": 8}
        code, plain = self.post(ask)
        self.assertEqual((code, plain["status"]), (200, "incomplete"))
        cut = plain["output"][-1]["content"][0]["text"]
        self.assertTrue(answer.startswith(cut) and cut != answer, cut)
        schema = {"type": "json_schema", "name": "x", "strict": True,
                  "schema": {"type": "object", "properties": {"a": {"type": "string"}}, "required": ["a"]}}
        for fmt in ({"type": "json_object"}, schema):
            with self.subTest(fmt=fmt["type"]):
                body = {**ask, "text": {"format": fmt}}
                code, r = self.post(body)
                self.assertEqual((code, r.get("status")), (200, "incomplete"), r)
                self.assertEqual(r["incomplete_details"], {"reason": "max_output_tokens"})
                self.assertIsNone(r["error"])
                # as a plain answer is cut: the words so far, and the item says it is not whole
                self.assertEqual([o["type"] for o in r["output"]], ["message"])
                self.assertEqual(r["output"][0]["status"], "incomplete")
                self.assertEqual(r["output"][0]["content"][0]["text"], cut)
                code, events = self.post({**body, "stream": True})
                self.assertEqual(code, 200)
                self.assertEqual([e["type"] for e in events],
                                 ["response.created", "response.in_progress", "response.output_item.added",
                                  "response.content_part.added", "response.output_text.delta",
                                  "response.output_text.done", "response.content_part.done",
                                  "response.output_item.done", "response.incomplete"])
                self.assertEqual(events[-2]["item"]["status"], "incomplete")
                final = events[-1]["response"]
                self.assertEqual((final["status"], final["incomplete_details"], final["error"]),
                                 ("incomplete", {"reason": "max_output_tokens"}, None))
                self.assertEqual(final["output"][0]["status"], "incomplete")
                self.assertEqual(final["output"][0]["content"][0]["text"], cut)


    def test_json_format_cut_in_the_thinking_has_no_message(self):
        self.say("Thinking about it for a while.\n</think>\n\n{\"a\": 1}")
        body = {"model": "m", "input": "json", "max_output_tokens": 8, "text": {"format": {"type": "json_object"}}}
        code, r = self.post(body)
        self.assertEqual((code, r.get("status")), (200, "incomplete"), r)
        self.assertEqual([(o["type"], o["status"]) for o in r["output"]], [("reasoning", "incomplete")])
        code, events = self.post({**body, "stream": True})
        self.assertEqual((code, events[-1]["type"]), (200, "response.incomplete"))


    def test_json_format_finished_answer_is_still_checked(self):
        # only the cap skips the check: an answer the model finished is still JSON, or 502, under a cap it did not reach
        body = {"model": "m", "input": "json", "reasoning": {"effort": "none"}, "max_output_tokens": 200,
                "text": {"format": {"type": "json_object"}}}
        self.say("{\"a\": 1}")
        code, r = self.post(body)
        self.assertEqual(code, 200, r)
        self.assertEqual((r["status"], r["output"][0]["status"]), ("completed", "completed"))
        self.say("not json")
        code, r = self.post(body)
        self.assertEqual((code, r["error"]["code"]), (502, "structured_output_failed"))
        code, events = self.post({**body, "stream": True})
        self.assertEqual(events[-1]["type"], "response.failed")
        self.assertEqual(events[-1]["response"]["error"]["code"], "structured_output_failed")


    def assert_cut_short(self, body, text):
        code, r = self.post(body)
        self.assertEqual(code, 200, r)
        self.assertEqual((r["status"], r["incomplete_details"]), ("incomplete", {"reason": "max_output_tokens"}))
        self.assertEqual([(o["type"], o["status"]) for o in r["output"]], [("message", "incomplete")])
        self.assertEqual(r["output"][0]["content"][0]["text"], text)


    def test_json_format_cut_right_after_whole_json_is_still_incomplete(self):
        # the check takes only finish stop, so the text can be whole JSON and is still not called finished
        self.say("{\"a\":1}xxxxxxxx")
        self.assert_cut_short({"model": "m", "input": "json", "reasoning": {"effort": "none"}, "max_output_tokens": 7,
                               "text": {"format": {"type": "json_object"}}}, "{\"a\":1}")


    def test_json_format_cut_with_no_cap_ends_incomplete(self):
        # the other length finishes, with no max_output_tokens: the same end as a plain answer
        plain = {"model": "m", "input": "json", "reasoning": {"effort": "none"}}
        body = {**plain, "text": {"format": {"type": "json_object"}}}
        answer = "{\"a\": \"" + "".join(f"{i:04d}" for i in range(100)) + "\"}"
        self.say(answer)
        self.post(body)
        self.engine.max_context = len(self.engine.last_prompt) + 8 + 30      # CTX_SLACK, and room for 30 tokens
        with self.subTest("full context"):
            self.assert_cut_short(body, answer[:30])
        self.engine.max_context = 16384
        self.svc.repeat_stop_tokens = 20
        self.say("{\"a\": \"" + "b" * 100)
        with self.subTest("repeat stop"):
            code, r = self.post(plain)
            cut = r["output"][0]["content"][0]["text"]
            self.assertLess(len(cut), 40, r)
            self.assert_cut_short(body, cut)


    def test_chat_json_format_cut_is_still_502(self):
        self.say("{\"a\": \"bcdefghijklmnopqrstuvwxyz\"}")
        body = {"model": "m", "messages": [{"role": "user", "content": "json"}], "max_tokens": 8,
                "response_format": {"type": "json_object"}}
        code, r = self.post(body, path="/v1/chat/completions")
        self.assertEqual((code, r["error"]["code"]), (502, "structured_output_failed"))
