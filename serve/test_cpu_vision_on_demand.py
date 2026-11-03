"""CPU on-demand lifecycle with fake encoders; no model, GPU, OS policy or force stop."""
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock
from serve import server
from serve.frontend import ChatTemplate
from serve.test_vision_elastic import ElasticVision
from serve.test_vram import VramEngine
from serve.test_graceful_engine_exit import Child

ROOT=Path(__file__).resolve().parents[1]


class CpuVisionOnDemand(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='cpu-vision-',dir=ROOT/'serve')
        self.addCleanup(self.tmp.cleanup)
        self.tok=server.ByteTokenizer()
        self.engine=VramEngine(self.tok);self.engine.loaded=True
        self.vision=ElasticVision(self.tmp.name);self.vision.gpu=False
        self.svc=server.Service(self.engine,self.tok,ChatTemplate(ROOT/'serve/chat_template.jinja'),vision=self.vision)
        self.addCleanup(self.drop_embeddings)

    def drop_embeddings(self):
        path=getattr(getattr(self.svc,'embeddings',None),'path',None)
        if path is not None:path.unlink(missing_ok=True)

    def picture(self):
        self.svc.prepare([{'role':'user','content':[{'type':'text','text':'image'},
                          {'type':'image','source':'x.png'}]}],None,{})

    def test_text_images_idle_reload_without_any_vram_call(self):
        self.engine.loaded=False
        with mock.patch.object(self.engine,'vram',side_effect=AssertionError('CPU resized VRAM')), \
                mock.patch.object(self.svc,'free_vram_mib',side_effect=AssertionError('CPU queried VRAM')):
            self.svc.ensure_loaded()
            self.svc.prepare([{'role':'user','content':'hello'}],None,{})
            self.assertEqual(self.vision.starts,0)
            self.picture();self.picture()
            self.assertEqual(self.vision.starts,1)
            self.assertFalse(self.svc.vision_held)
            self.assertEqual(self.svc._vision_idle_down(),'busy')
            self.svc.last_image_at=time.time()-61
            with self.svc.fifo:self.assertEqual(self.svc._vision_idle_down(),'busy')
            self.assertEqual(self.svc._vision_idle_down(),'down')
            self.assertEqual(self.svc._vision_idle_down(),'nothing')
            self.svc.ensure_loaded();self.assertEqual(self.vision.starts,1)
            self.picture();self.assertEqual(self.vision.starts,2)
            self.svc.unload();self.assertFalse(self.vision.alive())

    def test_opt_in_has_no_gpu_eligibility_bypass(self):
        self.assertTrue(server.Vision.elastic_enabled({'gpu':False,'elastic':True}))
        for value in (False,None,1,'yes'):
            self.assertFalse(server.Vision.elastic_enabled({'gpu':False,'elastic':value}))
        self.assertFalse(server.Vision.elastic_enabled({'gpu':True,'elastic':True}))
        self.assertFalse(server.Vision.elastic_enabled({'gpu':True,'elastic':True},'yes'))
        self.assertTrue(server.Vision.elastic_enabled({'gpu':True,'elastic':True},True))

    def test_cpu_default_eager_and_explicit_lazy_startup(self):
        cfg={'exe':'e','mmproj':'m','model':'t','gpu':False}
        with mock.patch.object(server.Vision,'work_dir',return_value=Path(self.tmp.name)), \
                mock.patch.object(server.Vision,'_start') as start:
            v=server.Vision(cfg)
            self.assertFalse(v.gpu or v.elastic);start.assert_called_once_with();start.reset_mock()
            v=server.Vision({**cfg,'elastic':True})
            self.assertTrue(v.elastic);self.assertFalse(v.gpu);start.assert_not_called()
            server.Vision(cfg,lazy=True);start.assert_not_called()

    def test_pending_cpu_owner_is_retried_not_reported_unloaded_or_replaced(self):
        p=Child(stuck=True);v=server.Vision.__new__(server.Vision)
        v.proc,v.stopped,v.elastic,v.gpu,v.elastic_idle_s=p,False,True,False,0.1
        v.on_cpu=False                          # new upstream fallback-state field, as initialized for a CPU reader
        self.svc.vision=v;self.svc.last_image_at=0
        try:
            with mock.patch.object(self.engine,'vram',side_effect=AssertionError('CPU resized VRAM')), \
                    mock.patch.object(v,'_start') as start:
                for attempt in range(2):
                    with self.assertRaises(server.EngineStuck):self.svc._vision_idle_down()
                self.assertEqual(p.waits,2)
                self.assertIs(v.proc,p);self.assertFalse(v.alive())
                with self.assertRaises(server.EngineStuck):self.svc._vision_up()
                start.assert_not_called()
                p.stuck=False
                self.assertEqual(self.svc._vision_idle_down(),'down')
                self.assertIsNone(v.proc)
        finally:
            p.stuck=False;server.graceful_engine_exit(p,1);p.stdout.close()


if __name__=='__main__':unittest.main()
