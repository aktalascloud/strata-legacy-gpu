"""Changed Responses route through the native MiniMax template/parser; no model or GPU."""
import json
from serve import frontend
from serve.minimax import NS
from serve.server import serve
from serve.test_minimax_frontend import service
from serve.test_responses import Server


class MiniMaxResponsesForce(Server):
    def setUp(self):
        self.svc = service(NS+'<content>x'+NS+'</content>'+NS+'</invoke>'+NS+'</tool_call>')
        self.engine, self.tok = self.svc.engine, self.svc.tok
        self.httpd = serve(self.svc, port=0)
        self.port = self.httpd.server_address[1]

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        frontend.use_family(None)

    def test_named_and_single_required_use_native_opening(self):
        tools=[{'type':'function','name':'files.write','parameters':{'type':'object','properties':{'content':{'type':'string'}}}}]
        for choice in ({'type':'function','name':'files.write'},'required'):
            with self.subTest(choice=choice):
                code, result=self.post({'input':'hi','tools':tools,'tool_choice':choice,
                                        'reasoning':{'effort':'none'},'max_output_tokens':128})
                self.assertEqual(code,200,result)
                call=result['output'][0]
                self.assertEqual((call['type'],call['name'],json.loads(call['arguments'])),
                                 ('function_call','files.write',{'content':'x'}))
                self.assertTrue(self.tok.decode(self.engine.last_prompt).endswith(
                    NS+'<tool_call>'+NS+'<invoke name="files.write">'))
