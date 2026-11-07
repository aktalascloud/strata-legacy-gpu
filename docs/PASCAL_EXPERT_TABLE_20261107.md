# P40 expert dispatch,7 November2026

Native `6c51f44c`, source `146df3c46873`. This own patch selects existing exact kernels per expert format and phase, without changing weights, routing or quantization. It keeps Q2_0 down on LDS8 while allowing faster EXPDEC GU; IQ4_NL down keeps its CUDA layout. Default off, opt-in for the qualified Swift first-install profile.

The complete code delta and guards are in [patch50](../performance/patches/series/50-pascal-expert-format-table/README.md). The other retained patches remain separately described in [the catalogue](../performance/patches/series/README.md).

## Operation evidence

112 layout/T/grid pairs compared direct and CUDA Graph output bitwise.130 Q8 shape/column checks (one expected shared-memory decline per mode) and27 actual package cases plus the full F32 check passed. The first successful Q8/one operator receipt was reused by exact native/driver/library/flag hashes after a log-header parser false positive; it is not represented as a second new run. CPUvision remained byte-identical.

Three rotating-weight direct CUDA-event timing rounds at T3, microseconds per complete expert operation:

| GU/down | Existing mode8 | Selected table | Throughput ratio |
|---|---:|---:|---:|
| 18/20 | 242.1 | 226.5 | +6.89% |
| 18/42 | 210.8 | 200.1 | +5.35% |
| 21/20 | 245.7 | 245.8 | -0.04% |
| 21/42 | 215.5 | 215.6 | -0.05% |
| 22/20 | 227.7 | 219.6 | +3.69% |
| 22/42 | 197.7 | 192.2 | +2.86% |
| 23/20 | 222.7 | 222.8 | -0.04% |

Direct timing includes host scheduling overhead. Graph output was checked; Graph timing was not measured. These percentages are not whole-model speedups and are not additive with dense-kernel gains.

## Matched model probe

Swift IQ3_S, same native, flag off/on: two excluded warmups and five512-token samples per initial arm, followed by five samples of the800-block variant and three measured return-control samples. Identical starting expert-profile SHA; no profile-save writes. Stored sampler retained, requests use temperature0/seed42 for repeatability. Initial/return-control medians39.3/37.8tok/s; the800-block variant also gave38.6. Combined eight-sample control and selected five-sample table medians 39.2→38.6tok/s (-1.53%), MAD 0.89%/1.55%, CPU 7.2%/7.1%. Same measured text/draft work: False. Established overall model TPS gain: False.

The selection retains the confirmed exact operation gain unless a credible model regression exceeds the saved rejection threshold. It does not establish an absolute maximum, long-context throughput or broad quality evaluation. Context262144/reserve150MiB/14workers/Q2 MTP/spec3/.5/suffix3/PCIe1/q4_0 KVhost20480grow/CPUvision/standard xhigh and all other user settings remain as saved. Author first-install sampling is T1/top_p.95/top_k20/min_p0.

The selected25-PR reading set is24/25 relevant scopes complete(96%); the broader source audit remains open. See [specific review findings](REVIEW_FOLLOWUP_20261107.md). Setup extraction/runtime checks do not prove a clean Windows normal install or administrator task registration.
