# Earlier DeepSeek AVX1/Pascal source and approximation trials

The current primary profile preserves native expert selection: see [exact P40 results](DEEPSEEK_EXACT_P40.md). PR821 below is a separate approximation experiment, disabled in that profile. Earlier numerical records remain historical.

Based on official Strata main `ffa80d73133ea5c548aefe57889a16e8085a938f`, fetched again on 4 November. The local engine is built for Ivy Bridge AVX1 and P40/sm61 with CUDA 12.9 and strict floating-point settings. The classic C8 release assets are unchanged. Portable DeepSeek binary packaging remains unqualified; model weights and private configuration are not included.

## Changes relative to official Strata

- Existing Pascal WMMA guards and `-dlcm=ca` cover the purposes of upstream #4300/#4301. No Tensor Core path is enabled on P40.
- Strict residency and read-ban guards cover CPU experts, embeddings and the external CPU vision projector. Engram has an explicit disk exception, but the selected local profile holds the full table in RAM. Genuine image-routing weights remain mandatory.
- The bounded profiler table fixes the #5127 host stage-array overwrite. The AVX1 Q8_K activation bridge preserves the qualified expert arithmetic; isolated operator gains are not model throughput gains.
- The Monitor has a RAM card and reports exact native expert-pool bytes, with a labelled rounded estimate for older engines.
- `STRATA_DS4_MTP_EXPERTS_CPU=1` places only Q2 MTP experts on CPU/RAM. Draft dense, attention and head stay on GPU. Default 0 preserves GPU placement. Locally this frees capacity for 1,975 main experts, versus 1,457 main plus 384 draft experts with GPU-MTP.
- [Maya PR821](https://github.com/mw00/project-maya/pull/821), head `5fbf23398007eb2821aa4b554993928680a8bd4c`, is adapted as an **opt-in approximate router**, under the retained MIT license. It substitutes eligible lower-ranked resident experts, protects rank-one and the strongest unbiased choice, retains native top-k normalization and uses original demand for cache heat. Prefill and the MTP drafter retain native routing. The local nonfinite fallback is preserved; the submitted config include is corrected for CUDA.

The approximate path is publicly OFF by default (`DS4_CACHE_SUB_RATIO=0` or absent). The selected local experiment uses ratio 0.5, 12 candidates, reference normalization and mass budget 0.3. The budget limits source-plus-replacement coefficient mass; it does **not** bound answer-quality loss. Enabled use requires one CUDA device, asynchronous strict-RAM routing and no helper/skip combination. Other backends and wider workloads are not qualified for enabled use.

## Actual local validation

CUDA 12.9/sm61 compilation passed. CPU configuration/protection tests and 20,000 randomized selector invariant cases passed. P40 execution passed 1,944 routing cases, including disabled-path bit parity, actual D5120/N384/T5 and boundary shapes. Existing unchanged numerical receipts were reused, not rerun or relabelled.

All three local arms passed five short synthetic quality checks: arithmetic, logic, ordering, exact JSON instructions, and a restricted Python function tested on three inputs. This small sample does not establish broad quality equivalence or perplexity.

| Comparison | Median decode |
| --- | ---: |
| Earlier same-binary GPU-MTP placement series | 11.01 tok/s |
| Earlier same-binary CPU-MTP placement series | 13.65 tok/s |
| Same-day exact C13 baseline before routing trial | 12.93 tok/s |
| Approximate budget 0.15, rejected | 12.41 tok/s |
| Approximate budget 0.3, earlier approximate selection | 13.71 tok/s |

Each arm uses one fixed prompt, two clean 128-token T1/topP1/effort-none samples and an excluded warmup; other CPU work was measured. Budget 0.15 regressed 4.02%. Budget 0.3 led the same-day baseline by 5.98%, but exceeded the earlier separate-series best by only 0.42%. Independent starts, cache placement and shared-PC variability limit causality. Neither a stable overall gain nor an absolute maximum is established. The earlier CPU/GPU placement comparison is separate; percentages must not be added.

## Selected local profile and limits

Context 262144; CPU 12; reserve 512 MiB; prefill-chunk 0; Q2 DSpark, block 5, confidence 0.5; CPU-only vision with 8 threads and max 1024. All 110,595,290,400 Engram bytes, CPU experts, embeddings and projector weights are resident in RAM. Routed experts use VRAM. Compressed four-bit KV stays on GPU, about 0.22 GiB; this native DeepSeek backend has no host-KV setting. Author T1/topP1/high75 remains unchanged; effort-none is a measurement override. Prefill-chunk 0 trades slower long-prompt ingestion for more expert capacity. Residency/read bans are enforced; these tests are not a per-file physical IO trace.

## Further source review

[Strata #4382](https://github.com/Niko1221/Strata/pull/4382) is an exact-arithmetic hyper-connection scheduling candidate, still awaiting P40 qualification. [#4367](https://github.com/Niko1221/Strata/pull/4367) is a sequential-load candidate; Windows and loaded-DSpark validation remain necessary. Maya #784 is Linux-only NUMA migration; #747 affects an unused prompt-flow path; #684 is draft-source telemetry, unnecessary while lookup is disabled. The fresh #4686 parser correction is covered by the retained canonical lookahead handling. Maya #827's poisoned-GPU recovery already exists locally. These are decisions for selected sources, not a completed review of all repositories. PR3957/3288 remain excluded; normal screening uses activity within 14 days.
