"""Deterministic parser-work regression, not a wall-clock performance threshold."""
import json,unittest
from unittest import mock
import serve.frontend as front

TOOLS=[{'name':'write_file','parameters':{'properties':{'content':{'type':'string'},'edits':{'type':'array'}}}}]
class RecoverScanWork(unittest.TestCase):
 def parse(self,key,value):
  counts={'call_end':0,'function_end':0,'param_chars':0}
  originals={n:getattr(front,n) for n in ['call_end','function_end','param_end']}
  def count(n):
   def wrapped(text,*args,**kwargs):
    if n=='param_end':counts['param_chars']+=len(text)
    else:counts[n]+=1
    return originals[n](text,*args,**kwargs)
   return wrapped
  raw='<tool_call><function=write_file><parameter='+key+'>\n'+value+'\n</parameter></function></tool_call>'
  with mock.patch.object(front,'call_end',count('call_end')),mock.patch.object(front,'function_end',count('function_end')),mock.patch.object(front,'param_end',count('param_end')):
   parser=front.OutputParser(thinking=False,tools=TOOLS,stream_tools=True,recover=True,declared_only=True);calls=[]
   for i in range(0,len(raw),8):calls += [e.call for e in parser.feed(raw[i:i+8]) if e.kind=='tool_call']
   calls += [e.call for e in parser.finish() if e.kind=='tool_call']
  self.assertEqual(len(calls),1)
  self.assertEqual(calls[0].arguments,{key:value if key=='content' else json.loads(value)})
  return counts
 def test_large_plain_string_has_bounded_structural_work(self):
  value='x'*32768;got=self.parse('content',value)
  self.assertLessEqual(got['call_end'],4);self.assertLessEqual(got['function_end'],4)
  self.assertLessEqual(got['param_chars'],20*len(value))
 def test_large_json_array_has_bounded_structural_work(self):
  value=json.dumps(['ordinary source text']*1500);got=self.parse('edits',value)
  self.assertLessEqual(got['call_end'],4);self.assertLessEqual(got['function_end'],4)
  self.assertLessEqual(got['param_chars'],20*len(value))
 def test_native_family_hook_keeps_recovery_dispatch(self):
  class Native(front.OutputParser):
   native_call_format=True
   def _body_end(self,body):return body.find('END_NATIVE')
  p=Native(thinking=False,recover=True);p.buf='payloadEND_NATIVE'
  self.assertEqual(p._wrapped_call_end(),7)
