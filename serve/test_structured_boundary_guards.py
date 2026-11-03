"""Boundary and shared-route guards for adapted structured output; no model/GPU."""
import json
import unittest
from serve import frontend, structured
from serve.server import serve, MockEngine
from serve.test_structured import Structured
from serve.test_minimax_frontend import service
from serve.minimax import NS
from serve.test_responses import Server


class ExtractionGuards(unittest.TestCase):
    def test_primitive_array_tails_and_excessive_depth_fail(self):
        _,validator=structured.prepare_format({'type':'json_object'},[])
        for text in ('[null,{"a":1},BROKEN]', '[false,{"a":1},]', '["text",{"a":1} BROKEN]',
                     '['*1500+'0,{"a":1}'+']'*1500):
            with self.subTest(text=text[:60]):
                with self.assertRaises(structured.StructuredOutputError):
                    structured.validated_json(text,validator,'stop')

    def test_prose_prefix_does_not_copy_every_remaining_suffix(self):
        class Counted(str):
            copied=0
            def strip(self,*args):return self
            def __getitem__(self,key):
                result=super().__getitem__(key)
                if isinstance(key,slice):self.copied+=len(result)
                return result
        text=Counted('[note] '*2048+'{"answer":1}')
        self.assertEqual(structured.extract_json(text),'{"answer":1}')
        self.assertLessEqual(text.copied,len(text)*2)  # operation-count guard, independent of PC timing/noise


class SharedRouteArrays(unittest.TestCase):
    setUp=Structured.setUp
    tearDown=Structured.tearDown
    request=Structured.request

    def test_responses_and_messages_do_not_discard_array_tail(self):
        self.svc.engine=MockEngine(self.tok,'</think>\n\n[{"a":1},{"a":2}]',max_context=16384)
        code,result=self.request('/v1/responses',{'input':'hi','reasoning':{'effort':'none'},
            'text':{'format':{'type':'json_object'}}})
        self.assertEqual((code,result['error']['code']),(502,'structured_output_failed'))
        code,result=self.request('/v1/messages',{'messages':[{'role':'user','content':'hi'}],'max_tokens':200,
            'output_config':{'effort':'none','format':{'type':'json_schema','schema':{'type':'object'}}}})
        self.assertEqual(code,200)
        self.assertIn('strata_structured_output_error',result)
        self.assertIn('[{"a":1},{"a":2}]',str(result['content']))


class MiniMaxChatFormatTools(Server):
    def setUp(self):
        self.svc=service(NS+'<tool_call>'+NS+'<invoke name="files.write">'+NS+'<content>x'+NS+'</content>'+NS+'</invoke>'+NS+'</tool_call>')
        self.engine,self.tok=self.svc.engine,self.svc.tok
        self.httpd=serve(self.svc,port=0);self.port=self.httpd.server_address[1]

    def tearDown(self):
        self.httpd.shutdown();self.httpd.server_close();frontend.use_family(None)

    def test_native_call_with_json_format_passes_whole_and_stream(self):
        tools=[{'type':'function','function':{'name':'files.write','parameters':{'type':'object','properties':{'content':{'type':'string'}}}}}]
        body={'messages':[{'role':'user','content':'hi'}],'reasoning_effort':'none','max_tokens':128,
              'tools':tools,'response_format':{'type':'json_object'}}
        code,result=self.post(body,path='/v1/chat/completions')
        self.assertEqual(code,200,result)
        call=result['choices'][0]['message']['tool_calls'][0]
        self.assertEqual((call['function']['name'],json.loads(call['function']['arguments'])),('files.write',{'content':'x'}))
        # Server.post decodes named SSE events, while chat uses data-only chunks: read chat through its HTTP fixture.
        import http.client
        connection=http.client.HTTPConnection('127.0.0.1',self.port,timeout=5)
        try:
            connection.request('POST','/v1/chat/completions',body=json.dumps({**body,'stream':True}),headers={'Content-Type':'application/json'})
            response=connection.getresponse();raw=response.read().decode()
            self.assertEqual(response.status,200)
            chunks=[json.loads(line[6:]) for line in raw.splitlines() if line.startswith('data: {')]
            self.assertEqual(chunks[-1]['choices'][0]['finish_reason'],'tool_calls')
            self.assertIn('files.write',raw)
            self.assertIn('data: [DONE]',raw)
        finally:connection.close()
