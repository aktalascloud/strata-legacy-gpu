"""Local safeguards for the adapted incomplete response, with synthetic faults only."""
from serve import frontend
from serve.server import serve
from serve.test_server import NonFiniteEngine
from serve.test_responses import Server
from serve.test_minimax_frontend import service


class NonFiniteJson(Server):
    def test_nonfinite_json_keeps_its_failure(self):
        for stream in (False,True):
            with self.subTest(stream=stream):
                self.svc.engine=NonFiniteEngine(self.tok,'{"a":"abcdefghijklmnopqrstuvwxyz"}',max_context=16384,plan=[8])
                code,result=self.post({'input':'hi','reasoning':{'effort':'none'},'max_output_tokens':100,
                    'text':{'format':{'type':'json_object'}},'stream':stream})
                if stream:
                    self.assertEqual(code,200)
                    self.assertEqual(result[-1]['type'],'response.failed')
                    self.assertEqual(result[-1]['response']['error']['code'],'structured_output_failed')
                else:
                    self.assertEqual((code,result['error']['code']),(502,'structured_output_failed'))
                self.assertEqual(len(self.svc.engine.calls),1)

    def test_plain_nonfinite_keeps_existing_incomplete_response(self):
        self.svc.engine=NonFiniteEngine(self.tok,'abcdefghijklmnopqrstuvwxyz',max_context=16384,plan=[8])
        code,result=self.post({'input':'hi','reasoning':{'effort':'none'},'max_output_tokens':100})
        self.assertEqual((code,result['status']),(200,'incomplete'))
        self.assertEqual(result['output'][0]['content'][0]['text'],'abcdefgh')


class MiniMaxPartialJson(Server):
    def setUp(self):
        self.svc=service('{"a":"abcdefghijklmnopqrstuvwxyz"}')
        self.engine,self.tok=self.svc.engine,self.svc.tok
        self.httpd=serve(self.svc,port=0);self.port=self.httpd.server_address[1]

    def tearDown(self):
        self.httpd.shutdown();self.httpd.server_close();frontend.use_family(None)

    def test_native_template_json_cap_is_incomplete(self):
        code,result=self.post({'input':'hi','reasoning':{'effort':'none'},'max_output_tokens':8,
                               'text':{'format':{'type':'json_object'}}})
        self.assertEqual((code,result['status']),(200,'incomplete'))
        self.assertEqual(result['output'][0]['status'],'incomplete')
        self.assertEqual(result['output'][0]['content'][0]['text'],'{"a":"ab')
