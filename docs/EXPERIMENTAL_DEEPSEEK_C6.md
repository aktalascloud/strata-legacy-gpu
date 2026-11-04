# DeepSeek AVX1/Pascal source and local experiments

This draft extends official Strata main `ffa80d73133ea5c548aefe57889a16e8085a938f`. The published classic C8 ZIP is unchanged and contains no portable DeepSeek runtime or weights. Local model acceptance is separate from portable release qualification.

## Useful changes

- Strict RAM loading, embeddings/read-ban guards, an Engram-only disk exception, CPU-only locked vision and genuine image-routing biases preserve the selected residency contract.
- The bounded profiler table prevents a host stage-array overwrite. The AVX1 Q8_K activation bridge reuses qualified expert arithmetic; its isolated operator speed factors are not model speedups.
- The Monitor has a RAM card and reports expert-pool size, using exact native bytes when available and a labelled rounded-log estimate otherwise.
- `STRATA_DS4_MTP_EXPERTS_CPU=1` places only Q2 draft experts in RAM/CPU. Draft dense, attention and head remain on GPU. Default0 preserves GPU placement. A matched two-sample 128-token T1/topP1/effort-none comparison measured 13.65 tok/s CPU-MTP versus11.01 GPU-MTP (+23.97%). This is one prompt on a shared Ivy Bridge/P40 PC, not a universal gain. CPU-MTP retained1975 main experts in VRAM versus1457 main plus384 draft experts in GPU mode. Confidence0.5 remained best stable tested setting;0.3 was slower and0.7 had mixed pairs.

## Experimental cache-aware expert substitution

Adapted from [Maya PR821](https://github.com/mw00/project-maya/pull/821), head `5fbf23398007eb2821aa4b554993928680a8bd4c`, under the retained Project Maya MIT license. This intentionally changes generated answers. It replaces eligible CPU-selected experts with lower-ranked resident experts. Rank-one and the strongest unbiased choice are protected; native top-k normalization is retained.

Public default is OFF (`DS4_CACHE_SUB_RATIO=0` or absent). The local trial starts with ratio0.5,12candidates and normalized source-plus-replacement mass budget0.15, stricter than the upstream0.1/0.6 experiment. Budget is not a probability or guarantee of answer quality. Prefill and the MTP drafter keep native routing. Original router demand drives cache heat, preventing replaced experts from disappearing from cache statistics. The local nonfinite-index fallback is preserved. The config header is included for CUDA, correcting the submitted HIP-only include location.

This adaptation refuses enabled use outside one CUDA device, strict copied RAM and asynchronous routing, and refuses helper/skip combinations. CUDA 12.9/sm61 compilation and CPU selector/config tests including 20,000 randomized invariant cases passed. On the P40, 1,944 routing cases passed, including native/off bit parity, actual D5120/N384/T5 and boundary shapes. Other backends are not qualified for enabled use.

The first local trial (ratio 0.5, mass budget 0.15) passed the same five short synthetic quality checks as the exact baseline: arithmetic, logic, ordering, exact JSON instructions and a restricted Python function with three inputs. This does not establish broad quality equivalence. Two clean matched T1/topP1/effort-none, 128-token samples measured 12.41 tok/s against the same-day exact C13 median 12.93 tok/s: a 4.02% regression. The 0.15 policy is rejected as the selected performance profile. A second conservative budget of 0.3 is being evaluated on the same binary; no gain is claimed. AMD results from the upstream PR are not P40 evidence.

The new headers/selectors retain Maya's policy. Other backends are not qualified for this opt-in path. Original MIT/dependency licenses remain unchanged.

## Current local profile

Context262144, CPU12, reserve512MiB, prefill-chunk0, Q2 DSpark/block5/confidence0.5, CPU-only vision8/max1024. All Engram110595290400bytes, CPU experts, embeddings and projector weights are resident in RAM; routed experts use VRAM. The compressed four-bit KV cache remains on GPU (about0.22GiB); the native DeepSeek backend has no host-KV setting. The author default remains T1/topP1/high75; effort-none is a measurement override. Prefill-chunk0 sacrifices long-prompt ingestion speed for expert capacity. Other applications and system hardware policies remain untouched.

Not qualified here: portable DeepSeek packaging, broad quality/perplexity, every model/tool/image workload, all source repositories or an absolute generation maximum.
