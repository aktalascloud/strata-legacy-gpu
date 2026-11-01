"""Actual ephemeral HTTP/MockEngine checks; never connects to the model or port8093."""
import contextlib
import copy
import http.client
import io
import json
from pathlib import Path
import sys
import time
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
sys.path[:0] = [str(BASE), str(BASE / 'tools')]
from serve import server
from serve.frontend import ChatTemplate, anthropic_to_messages

ARGS = '<parameter=zone>\nUTC\n</parameter>\n</function>\n</tool_call>'


class Engine(server.MockEngine):
    failure = None
    forcing = False

    def generate(self, ids, *args, **kwargs):
        if self.forcing:
            prompt = self.tok.decode(ids)
            text = ARGS if prompt.endswith('<function=clock>\n') else '<function=clock>\n' + ARGS
            self.script = self.tok.encode(text, parse_special=True) + self.tok.encode(server.IM_END, parse_special=True)
        tokens = list(super().generate(ids, *args, **kwargs))
        if tokens:
            yield tokens[0]
        if self.failure:
            raise self.failure
        yield from tokens[1:]


class API(unittest.TestCase):
    def setUp(self):
        self.tok = server.ByteTokenizer()
        self.engine = Engine(self.tok, 'ordinary answer', max_context=4096)
        self.svc = server.Service(self.engine, self.tok, ChatTemplate(HERE / 'chat_template.jinja'))
        self.httpd = server.serve(self.svc, port=0)
        self.port = self.httpd.server_address[1]
        self.assertNotEqual(self.port, 8093)

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()

    def post(self, path, body):
        c = http.client.HTTPConnection('127.0.0.1', self.port, timeout=15)
        try:
            c.request('POST', path, json.dumps(body), {'Content-Type': 'application/json'})
            r = c.getresponse()
            return r.status, dict(r.getheaders()), r.read()
        finally:
            c.close()

    def test_parallel_result_ids_and_safe_incomplete_fallback(self):
        raw = [
            {'role': 'user', 'content': 'read both'},
            {'role': 'assistant', 'content': [
                {'type': 'tool_use', 'id': 'slow', 'name': 'read', 'input': {'p': 'slow'}},
                {'type': 'tool_use', 'id': 'fast', 'name': 'read', 'input': {'p': 'fast'}}]},
            {'role': 'user', 'content': [
                {'type': 'tool_result', 'tool_use_id': 'fast', 'content': 'RESULT_FAST'},
                {'type': 'tool_result', 'tool_use_id': 'slow', 'content': 'RESULT_SLOW'}]}]
        before = copy.deepcopy(raw)
        for stream in (False, True):
            code, _, _ = self.post('/v1/messages', {'model': 'mock', 'messages': raw, 'max_tokens': 32,
                                                   'thinking': {'type': 'disabled'}, 'stream': stream})
            self.assertEqual(code, 200)
            prompt = self.tok.decode(self.engine.last_prompt)
            self.assertLess(prompt.index('RESULT_SLOW'), prompt.index('RESULT_FAST'))
        self.assertEqual(raw, before)
        malformed = copy.deepcopy(raw)
        malformed[2]['content'][0]['tool_use_id'] = 'unknown'
        got = anthropic_to_messages({'messages': malformed})[0]
        self.assertEqual([m['content'] for m in got if m['role'] == 'tool'], ['RESULT_FAST', 'RESULT_SLOW'])
        self.assertFalse(any('_call_id' in m for m in got))

    def test_error_envelope_preserves_status_retry_header_and_other_routes(self):
        for path in ('/v1/messages', '/v1/v1/messages/count_tokens?beta=true'):
            code, _, raw = self.post(path, {'messages': 5, 'max_tokens': 8})
            self.assertEqual(code, 400)
            self.assertEqual(json.loads(raw)['type'], 'error')
        body = {'messages': [{'role': 'user', 'content': 'hi'}], 'max_tokens': 8}
        with mock.patch.object(self.svc, 'load', side_effect=server.GpuBusy('synthetic busy', retry_after=7)):
            code, headers, raw = self.post('/v1/messages', body)
        self.assertEqual((code, headers.get('Retry-After')), (503, '7'))
        err = json.loads(raw)
        self.assertEqual((err['type'], err['error']['type']), ('error', 'server_error'))
        code, _, raw = self.post('/v1/chat/completions', {'messages': 5})
        self.assertEqual(code, 400)
        self.assertNotIn('type', json.loads(raw))

    def test_started_stream_errors_and_admission_drain(self):
        self.engine.failure = server.GpuBusy('synthetic busy')
        cases = [('/v1/chat/completions', {'messages': [{'role': 'user', 'content': 'hi'}]}, b'data: [DONE]'),
                 ('/v1/messages', {'messages': [{'role': 'user', 'content': 'hi'}]}, b'event: error'),
                 ('/v1/responses', {'input': 'hi', 'store': False}, b'event: response.failed')]
        for path, body, final in cases:
            code, _, raw = self.post(path, {**body, 'model': 'mock', 'stream': True, 'max_tokens': 32,
                                           'max_output_tokens': 32, 'reasoning_effort': 'none',
                                           'thinking': {'type': 'disabled'}})
            self.assertEqual(code, 200, raw)
            self.assertNotIn(b'HTTP/1.', raw)
            self.assertIn(final, raw)
            self.assertIn(b'synthetic busy', raw)
            self.assertEqual(self.svc.wait_for_drain(1), 0)
        self.engine.failure = RuntimeError('synthetic private detail')
        code, _, raw = self.post('/v1/chat/completions', {'messages': [{'role': 'user', 'content': 'hi'}],
                                                        'stream': True, 'max_tokens': 32})
        self.assertEqual(code, 200)
        self.assertIn(b"server's log", raw)
        self.assertNotIn(b'private detail', raw)
        self.assertEqual(self.svc.wait_for_drain(1), 0)
        self.assertEqual(self.svc.begin_drain(), 0)
        self.assertEqual(self.svc.wait_for_drain(1), 0)
        code, _, raw = self.post('/v1/chat/completions', {'messages': [{'role': 'user', 'content': 'hi'}]})
        self.assertEqual(code, 503)
        self.assertIn(b"drain", raw.lower())

    def test_required_many_and_named_one_keep_declared_calls(self):
        self.engine.forcing = True
        tools = [{'type': 'function', 'function': {'name': name, 'parameters': {
            'type': 'object', 'properties': {'zone': {'type': 'string'}}}}} for name in ('clock', 'weather')]
        for offered, choice, suffix in [(tools, 'required', '<tool_call>\n'),
                                        (tools[:1], 'required', '<function=clock>\n')]:
            code, _, raw = self.post('/v1/chat/completions', {'messages': [{'role': 'user', 'content': 'time'}],
                                                            'tools': offered, 'tool_choice': choice, 'max_tokens': 128,
                                                            'reasoning_effort': 'none'})
            self.assertEqual(code, 200, raw)
            data = json.loads(raw)
            self.assertEqual(data['choices'][0]['finish_reason'], 'tool_calls', raw)
            call = data['choices'][0]['message']['tool_calls'][0]['function']
            self.assertEqual((call['name'], json.loads(call['arguments'])), ('clock', {'zone': 'UTC'}))
            self.assertTrue(self.tok.decode(self.engine.last_prompt).endswith(suffix))


if __name__ == '__main__':
    unittest.main(verbosity=2)
