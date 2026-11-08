# CUDA Graph upload on Tesla P40,8 November2026

[FreeToken97](https://github.com/gdevenyi/FreeToken/pull/97), exact head `77874d22da600c5fb2220707b1333b63bc98fa92`, all3 changed-file diffs/body read. The source offers an upload switch; its reported RTX5080/PyTorch gain does not qualify the CUDA12.9/P40 path.

| Graph nodes | Words | Work/word | Upload on,us | Upload off,us | Off throughput change |
|---:|---:|---:|---:|---:|---:|
| 128 | 4096 | 1 | 168.028 | 173.173 | -2.97% |
| 128 | 65536 | 16 | 238.124 | 233.865 | +1.82% |
| 512 | 4096 | 1 | 636.236 | 709.104 | -10.28% |
| 512 | 65536 | 16 | 896.088 | 897.552 | -0.16% |
| 1024 | 4096 | 1 | 1412.240 | 1442.890 | -2.12% |
| 1024 | 65536 | 16 | 1802.827 | 1788.380 | +0.81% |

6 alternating rounds per shape,3 warmup launches,32 timed launches/round,CUDA events; bitwise uint32 output comparison. Timing raw round samples were not persisted, so no confidence interval is asserted.

Six output comparisons were bitwise identical. This synthetic graph contains no model, PLE or host WAIT.4/6 shapes were slower with upload disabled. No whole-model improvement is established, so the existing upload behavior and all user parameters are retained. No new production feature/patch was selected.

Current Strata CUDA defaults early-PLE mode0; a lazy first upload could interact with its host-published flag. That requires its own cold-first-launch proof before any production opt-out. The probe does not establish that safety.

The model was drained/restored through schema3 and normal startup, with no forced stop. Native/CPUvision/sampler/route0/context262144/reserve150MiB and all saved settings remained unchanged. Broader source review remains open; this pass has14 records,11 complete changed-file scopes and3 bounded/partial scopes. Inventory is not code review.
