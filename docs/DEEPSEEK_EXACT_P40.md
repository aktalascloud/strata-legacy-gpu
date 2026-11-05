# Exact DeepSeek 1017 scheduling and router storage on P40

The newer selected CPU-memory placement is documented in [CPU RAM lock](DEEPSEEK_CPU_RAM_LOCK.md). C16 measurements below remain historical and are not retagged as new tests.

These optional paths keep original coefficients and native routing. They do not requantize weights or replace selected experts. Public defaults remain off; only the local CUDA 12.9/sm61/Ivy Bridge configuration is qualified. Other backends and multi-GPU execution are not newly validated.

## HC scheduling

`STRATA_DS4_HC_SPLIT_PARALLEL=1` adapts [Strata #4382](https://github.com/Niko1221/Strata/pull/4382), head `9bc42f77092e33610b62f04b8bd9c0c74401310c`. The current Sinkhorn split runs beside normalization that reads the preceding sublayer's pre values. Those allocations are distinct. The original kernels/counters and disabled path remain available.

Actual P40 execution passed 24 bit-parity/canary cases at D5120, H4, T1/5/16, RMS epsilon 1e-20 and 20 Sinkhorn iterations. HC operation latency fell from 28.91 to 20.69 microseconds at T1, and from 42.79 to 34.19 microseconds at T5, in a bounded ABBA screen. These are operator timings, not whole-model gains. A first host-only diagnostic omitted the INFO prefix; this candidate corrects it. No old qualification receipt was rewritten.

The published HC fixture uses a reference namespace. For reproduction, compile original kernels from public baseline `c7d20fd4ffa3237b6bb216f6cab8b7fb78208987` with `-Dds4=hc_reference`, then link that object, the new production kernel object and the fixture. Use the same CUDA12.9/sm61/CA, AVX1 and strict-FP profile. No model is needed for this fixture.

## Router memory

`STRATA_DS4_ROUTER_BF16=1` keeps the original BF16 router bits in VRAM. Each coefficient expands to exactly the same F32 bit pattern when loaded into a register. Four explicit F32 FMAs and the warp reduction retain their old order. Original F32 router sources, including the draft layers, retain the original path. This uses integer loads/bit casts and F32 arithmetic, not BF16 hardware or Tensor Cores.

The selected pack has 40 main BF16 routers: avoiding their load-time F32 expansion saves 157,286,400 bytes (150 MiB). Actual P40 execution compared original F32 and compact storage on existing layers0,19,39 at N384/D5120/T1,5,16. All27 cases and76,032 finite outputs matched bit for bit; bounds remained intact. No weights were copied to new files. Router operation latency fell about42% at T1 and46% at T5 in a bounded ABBA screen. The amount of extra expert capacity and end-to-end throughput remain model-load measurements, not deductions from these percentages.

The router fixture takes three existing shard paths and absolute byte offsets from a matching pack's tensor index. It reads only those three BF16 tensors into memory. It does not download, modify or dump weights.

## Earlier C16 selected profile

Context262144, CPU12, reserve384MiB, prefill-chunk0, Q2 MTP experts on CPU/RAM, confidence0.5, CPU-only locked vision, HC1 and compact-router1. DS4_CACHE_SUB_RATIO=0 explicitly preserves native expert selection. Author T1/topP1/high75 remains unchanged. Swift/DavidAU settings remain unchanged.

Actual readback reports 2,010 main experts in VRAM, versus1,975 previously:35 additional experts. Expert pool17618411520bytes;40 BF16 routers save157286400bytes. All13,734 CPU experts, full110595290400-byte Engram table, embeddings and the CPU projector remain resident. Compressed four-bit KV remains on GPU; no host-KV support is implied. Reserve384 loaded and generated successfully; the512 fallback was not needed. About120MiB GPU space remained after the bounded acceptance probe. Lower reserve values are not qualified.

After an initial nonstationary screen, a balanced confirmation used one fixed prompt,128 API tokens per request,T1/topP1,request effort-none and measured other CPU load:

| MTP confidence | Two decode samples, tok/s | Median |
| --- | --- | ---: |
| 0.3 | 12.28 / 13.39 | 12.84 |
| 0.5 | 14.05 / 13.44 | 13.74 |
| 0.7 | 13.30 / 14.14 | 13.72 |

Confidence0.3 was slower;0.7 had mixed pairs and no stable gain.0.5 is retained. The earlier separate exact-series best was13.65tok/s, nearly the same. Neither a stable overall throughput gain nor an absolute maximum is established; operator latency reductions must not be added or presented as whole-model percentages. Warmup/cache placement and shared-PC variation remain material. The earlier16–18tok/s approximate trial is not a quality-equivalent comparison.

One synthetic1024x1024red image exercised the lower reserve and unchanged CPU-only projector. The final answer correctly named red, with671 prompt tokens and positive MTP acceptance. This is headroom/functional evidence, not a vision-speed benchmark or a full1024-image-token/262K-context test. All actual INFO mode values, including zero substitution ratio, were read back. The new router's FMA/reduction order and coefficients are unchanged; moving experts between CPU/GPU retains the native framework's rounding behavior. Broad semantic quality and full-length-context throughput are not newly measured.

## Native component release scope

The separately staged native ZIP contains the tested engine/CPU vision binaries and allowed CUDA/LLVM libraries, with licenses and per-file hashes. It excludes weights, private configuration, Python/server, toolchains and Microsoft runtime DLLs. A compatible installed Microsoft x64 runtime and CUDA driver are prerequisites; on this host the system Microsoft DLLs matched the qualified inputs by SHA. Staged version/import resolution and privacy checks passed; ZIP CRC/member SHA are independently checked. It is a native-component prerelease, not a fresh Windows installation or a complete portable application acceptance.

## Remaining work

CPU worker10 versus selected12 is not yet measured on this exact profile; earlier worker14 screening does not prove a universal optimum. Windows/full-RAM/DSpark adaptation of loader4367, wider applicable recent1017source review, broad quality/full-context workloads and complete portable desktop switching remain separate work. PR3957/3288 remain excluded. No system NUMA, affinity, clock, power, driver or unrelated-service setting was changed.
