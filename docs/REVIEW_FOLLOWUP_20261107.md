# AVX1 / P40 follow-up review

This follow-up separates reading code, qualifying a kernel, and measuring model decode. Metadata/applicability inventory is not a complete semantic audit. The activity window is two calendar months; Strata3288/3957 remain excluded.

The selected25-PR set has24 completed relevant reading scopes and1 explicitly partial scope (96% of this set only). This is not a global completion percentage or a security sign-off for every file in those repositories. The initial10-revision set and exact-warp measurements are documented in [the dense scheduling report](PASCAL_EXACT_WARP_20261107.md).

| Revision | Findings and disposition |
|---|---|
| [Strata5493](https://github.com/Niko1221/Strata/pull/5493), `ffd6c47e` | Full3-file parser diff plus isolated fixtures: duplicate nonadjacent array parameters produce3 stream/whole mismatches; nullable array `null` is also dropped. Full proposal not selected. |
| [Strata5495](https://github.com/Niko1221/Strata/pull/5495), `566a9625` | Server and fake-reader tests read. Peer cancellation adds a forced kill and permits restart after an unproved wait timeout. Incompatible with the retained graceful owner contract. |
| [Strata5498](https://github.com/Niko1221/Strata/pull/5498), `dbc14f92` | All5 diffs read. Turing register-prefetch uses MMA/ldmatrix instructions unavailable on P40; no Tensor Core code enabled. |
| [Strata5479](https://github.com/Niko1221/Strata/pull/5479), `59f6da53` | All3 diffs read. Name-only PLE shard exemption bypasses split consistency without proving tensor payload/family equivalence. Current Swift already has a qualified PLE. |
| [Strata4928](https://github.com/Niko1221/Strata/pull/4928), `75d96ac4` | Long lookup over a multi-GPU layer split is outside the current single-P40/spec3 path. Original bounds retained. |
| [Strata5492](https://github.com/Niko1221/Strata/pull/5492), `93f0a5fc` | Full updater and fixture diffs read. Resolves stale Control version paths; this distribution uses its separate immutable runtime and owner guards. No decode benefit claimed. |
| [Strata5477](https://github.com/Niko1221/Strata/pull/5477), `dd2a60c5` | Complete model-retrieve route/tests read. Optional API feature, no generation-speed gain; not selected in this performance pass. |
| [Strata207](https://github.com/Niko1221/Strata/pull/207), `5a3c98e8` | Complete diff read. T0 row-prefetch principle already exists in the current AVX1 decoder; no duplicate patch or new percentage claimed. |
| [Strata1316](https://github.com/Niko1221/Strata/pull/1316), `1ec94221` | Complete policy/tests read. Fresh main already preserves stale full-chain re-probing with newer banked costs. Current lookup-chain remains0. |
| [Strata1415](https://github.com/Niko1221/Strata/pull/1415), `1ba010ef` | All7 changed code/test/report scopes read. Preserving ggml reduction order is useful; the AVX2/FMA implementation cannot be imported into the Ivy Bridge baseline. Existing native AVX1 arithmetic is retained. |
| [Strata4065](https://github.com/Niko1221/Strata/pull/4065), `0b2e1cdd` | All4 diffs and current copy ownership read. Parallel startup fill needs a CUDA-only/nibble-aware adaptation: the HIP blocking-copy implementation shares a staging buffer. No startup or decode gain established here. |
| [Strata4844](https://github.com/Niko1221/Strata/pull/4844), `7faa5b98` | Complete diff read. Main already retains the pending adaptive-round publication fix through `whole_round`; obsolete scalar range fields are not restored. |
| [Strata4158](https://github.com/Niko1221/Strata/pull/4158), `a8340321` | All5 diffs, including full parity fixture, read. Small-chunk MMVQ adds Q8_1 activation quantization; the fixture allows2% RMS/5% max error. Not selected under the preserved-quality requirement. |

Additional full-scope disposition and the remaining partial scope:

- [Strata2522](https://github.com/Niko1221/Strata/pull/2522), `9a54a13f`: all15 changed diffs read, including SYCL, documentation and the complete external handoff helper. The changed read loop drops the absolute deadline for unrelated log lines; the short partial-result fallback also needs protocol ownership review. The helper also needs filename containment and failure restoration; it was never run. Elastic VRAM is not enabled here.
- [Strata5500](https://github.com/Niko1221/Strata/pull/5500), `4277f9d2`: cache/control, memory and snapshot scopes read; substantial persistence/server/test scopes remain unread. Tolerant restore bypasses a checkpoint prefix/stage mismatch; no broad storage prototype was imported into the RAM-first profile.

Kobold's complete Hybrid MoE patch was read through its worker barriers, admission/upload lifetime and final CPU-output copy. Its broad CPU/GPU overlap is already provided by Strata's native pool; missing experts are not substituted. The complete Haswell dot patch requires AVX2/FMA, so its binary code is not enabled on AVX1. No untested model speed percentage is inferred from either source.

Own P40 expert-dispatch experiments keep weights and router choices unchanged and compare the actual cached mode8 baseline with EXPDEC, including the existing strided path. The early MINB/MINBLK pass that did not actually execute EXPDEC is withdrawn, as recorded in the dense scheduling report. Numerical direct/Graph qualification and whole-model timing are reported separately when selected.
