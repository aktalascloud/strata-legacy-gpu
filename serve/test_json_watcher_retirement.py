"""Run actual Handler methods with an isolated socket/response harness; no model or process control."""
import ast,io,json,socket,threading,types,sys
from pathlib import Path
def probe(source):
 tree=ast.parse(source);wanted={}
 for n in ast.walk(tree):
  if isinstance(n,ast.FunctionDef)and n.name in{'_watch_client','_json'}:wanted[n.name]=n
 assert set(wanted)=={'_watch_client','_json'}
 rows=[]
 for case in ['complete_then_close','early_EOF','write_failure']:
  closed=threading.Event();exited=threading.Event();cancel=threading.Event();svc=types.SimpleNamespace(status_lock=threading.RLock(),active_cancels=set(),disconnects=0)
  def disconnected(event):svc.disconnects+=1;event.set()
  svc.note_client_disconnect=disconnected
  real_thread=threading.Thread
  def thread(*args,**kw):
   target=kw['target']
   def observed():
    try:target()
    finally:exited.set()
   kw['target']=observed;return real_thread(*args,**kw)
  env=dict(threading=types.SimpleNamespace(Event=threading.Event,Lock=threading.Lock,Thread=thread),socket=socket,select=types.SimpleNamespace(select=lambda *a:([1]if closed.is_set()else[],[],[])),svc=svc,json=json,V1_V1_ALIASES={})
  cls=ast.ClassDef(name='Handler',bases=[],keywords=[],body=list(wanted.values()),decorator_list=[]);module=ast.fix_missing_locations(ast.Module(body=[cls],type_ignores=[]));exec(compile(module,'actual-handler','exec'),env)
  h=env['Handler']();h.path='/v1/chat/completions';h.record=None;h.connection=types.SimpleNamespace(recv=lambda *a:b'');h._note=lambda **kw:setattr(h,'outcome',kw.get('outcome'));h.send_response=lambda *a:None;h.send_header=lambda *a:None;h.end_headers=lambda:None;h._cors=lambda:None
  def write(data):
   if case=='write_failure':raise BrokenPipeError('isolated write failure')
   closed.set();assert exited.wait(2),'Watcher did not exit after final body'
  h.wfile=types.SimpleNamespace(write=write);h._watch_client(cancel);write_failed=False
  try:
   if case=='early_EOF':closed.set();assert exited.wait(2)
   else:
    try:h._json(200,{'choices':[]})
    except BrokenPipeError:write_failed=True
   rows.append(dict(case=case,cancelled=cancel.is_set(),disconnects=svc.disconnects,write_error_propagated=write_failed))
  finally:h.watch_done.set();assert exited.wait(2)
 return rows
import unittest
class JsonWatcherRetirement(unittest.TestCase):
 def test_completed_body_early_EOF_and_write_failure(self):
  rows=probe(Path(__file__).with_name('server.py').read_text(encoding='utf-8-sig'))
  self.assertEqual(rows,[dict(case='complete_then_close',cancelled=False,disconnects=0,write_error_propagated=False),dict(case='early_EOF',cancelled=True,disconnects=1,write_error_propagated=False),dict(case='write_failure',cancelled=False,disconnects=0,write_error_propagated=True)])
if __name__=='__main__':unittest.main()
