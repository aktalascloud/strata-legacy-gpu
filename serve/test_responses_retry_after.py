"""PR4833 refused-load HTTP header; no GPU/model."""
import json
import urllib.request
import urllib.error
from serve.test_server import SharingTheGpu

class ResponsesRetryAfter(SharingTheGpu):
    def test_gpu_refusal_on_responses_sends_retry_after_too(self):
        """The same refusal as above on /v1/responses: docs/DETAILS.md promises the header with no route limit."""
        self.svc.min_free_vram_mib = 8000
        self.svc.free_vram_mib = lambda: 2000
        self.svc.vram_free_wait_s = 0.2                              # (not the 15 s wait for memory)
        for stream in (False, True):
            with self.subTest(stream=stream):
                self.svc.unload()
                r = urllib.request.Request(self.base + "/v1/responses",
                                           data=json.dumps({"model": "m", "input": "hi", "stream": stream}).encode(),
                                           headers={"Content-Type": "application/json"}, method="POST")
                with self.assertRaises(urllib.error.HTTPError) as caught:
                    urllib.request.urlopen(r, timeout=30)
                with caught.exception as e:
                    self.assertEqual(e.code, 503)
                    self.assertEqual(e.headers["Retry-After"], "15")
                    self.assertIn("in use by another program", json.loads(e.read())["error"]["message"])
                self.assertEqual(self.engine.starts, 0)
