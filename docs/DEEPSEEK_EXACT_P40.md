# Exact DeepSeek 1017 scheduling and router storage on P40

These optional paths keep original coefficients and native routing. They do not requantize weights or replace selected experts. Public defaults remain off; only the local CUDA 12.9/sm61/Ivy Bridge configuration is qualified. Other backends and multi-GPU execution are not newly validated.

## HC scheduling

`STRATA_DS4_HC_SPLIT_PARALLEL=1` adapts [Strata #4382](https://github.com/Niko1221/Strata/pull/4382), head `9bc42f77092e33610b62f04b8bd9c0c74401310c`. The current Sinkhorn split runs beside normalization that reads the preceding sublayer's pre values. Those allocations are distinct. The original kernels/counters and disabled path remain available.

Actual P40 execution passed 24 bit-parity/canary cases at D5120, H4, T1/5/16, RMS epsilon 1e-20 and 20 Sinkhorn iterations. HC operation latency fell from 28.91 to 20.69 microseconds at T1, and from 42.79 to 34.19 microseconds at T5, in a bounded ABBA screen. These are operator timings, not whole-model gains. A first host-only diagnostic omitted the INFO prefix; this candidate corrects it. No old qualification receipt was rewritten.

The published HC fixture uses a reference namespace. For reproduction, compile original kernels from public baseline `c7d20fd4ffa3237b6bb216f6cab8b7fb78208987` with `-Dds4=hc_reference`, then link that object, the new production kernel object and the fixture. Use the same CUDA12.9/sm61/CA, AVX1 and strict-FP profile. No model is needed for this fixture.

## Router memory

`STRATA_DS4_ROUTER_BF16=1` keeps the original BF16 router bits in VRAM. Each coefficient expands to exactly the same F32 bit pattern when loaded into a register. Four explicit F32 FMAs and the warp reduction retain their old order. Original F32 router sources, including the draft layers, retain the original path. This uses integer loads/bit casts and F32 arithmetic, not BF16 hardware or Tensor Cores.

The selected pack has 40 main BF16 routers: avoiding their load-time F32 expansion saves 157,286,400 bytes (150 MiB). Actual P40 execution compared original F32 and compact storage on existing layers0,19,39 at N384/D5120/T1,5,16. All27 cases and76,032 finite outputs matched bit for bit; bounds remained intact. No weights were copied to new files. Router operation latency fell about42% at T1 and46% at T5 in a bounded ABBA screen. The amount of extra expert capacity and end-to-end throughput remain model-load measurements, not deductions from these percentages.

The router fixture takes three existing shard paths and absolute byte offsets from a matching pack's tensor index. It reads only those three BF16 tensors into memory. It does not download, modify or dump weights.

## Local parameter trial

The pending combined trial keeps context262144, CPU12, Q2 MTP experts on CPU/RAM, CPU-only locked projector, full Engram and other weights resident, and author T1/topP1/high75. It tests reserve384 MiB, with a guarded512 fallback only after proven failed-owner closure. Swift's reserve150 and other saved models are unchanged. Exact native expert selection is the primary quality-preserving control; the earlier PR821 substitution remains a separate approximation experiment.

Native INFO now reports HC mode, router storage/count/saved bytes and the actual substitution ratio. Whole-model residency, expert count, confidence0.3/0.5/0.7 screening and final selection are pending. Existing unchanged CPU/expert/router proofs are reused rather than rerun. No absolute generation maximum, universal quality equivalence or portable clean-install result is claimed.
