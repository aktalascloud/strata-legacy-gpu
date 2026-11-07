# Keep the long lookup without CUDA Graph churn

Selected first-install Swift preset adds --lookup-sizes4,12. MTP/spec3 retains sizes1/2/3; lookups retain4and12. The competing intermediate size5 is omitted. Context262144, reserve150MiB,9249 expert slots, weights and sampler remain unchanged. Existing user configuration is preserved.

On predecessor native6c51, the same512-token series recorded0 graph reclaims versus21 without this mask; median39.0tok/s versus38.6 was within noise. A23999-token cold/cached memory probe completed at42.8/47.3decode tok/s with0reclaims. These are explicitly predecessor/profile receipts, not new-native long-context timings or a full262144 throughput test. Current same-native H2 probe retains this graph set and its zero-reclaim selection gate.

KVhost20480 means cells per QSA layer, with the full KV copy in pinned RAM. Host streaming uses a fixed VRAM pool; --kv-grow is ineligible with positive kv_resident. No global CUDA loading mode, memory reserve, driver or OS policy is changed. Factory defaults only; no second user configuration is introduced.

# Exact fused expert half-warps on Pascal

Selected in the main Swift profile and first-install preset with STRATA_SM61_FUSED_H2=1. Adapted from Niko1221/Strata#5033 at06d119bce57539b70b717b187f0e03049e95dbac (MIT), to the used mode8 fused GU/SwiGLU/Q8 path. The PR's separate mode7 flag alone would not reach this path.

Each physical half-warp carries two original logical lanes independently and replays XOR16/8/4/2/1. Weights, router choices, dot products, nonlinear epilogue and quantization remain unchanged. Guard: sm61/experimentalCUDA, auto mode8, GU21/down20or42,2560x640, nonstrided capacity10/20/30/40. Manual modes, old/v1, Hadamard, nibble and other GPUs retain the old path. Default remains off outside the qualified preset.

Detached240 direct/Graph cases match raw prequantization values and Q8 bytes; reference Q8 matches the actual preceding6c51 archive. Six alternating Graph timing rounds over rotating weight blobs show GU throughput+10.8..13.2%. Actual final native8cc3edf0 passed56 layout/T/grid pairs direct/Graph,130 Q8 checks (one expected shared-memory decline per mode), and27 required package cases including fullF32. Operation percentages are not whole-model gains or additive with previous patches.

Same-native Swift off/on, two warmups plus five512-token measurements per arm: medians39.3/39.1tok/s, observed-0.51%, MAD1.27/0.26%, CPU7.3/7.3%. Identical text/draft work:False. Established whole-model TPS gain:False. Selection retains a confirmed exact operation gain absent a credible model regression. This is not an absolute maximum or a broad quality evaluation.

Base public revision9b5c9057ed256363d670c0a2e6c50f97d8207fb4, official source146df3c468739147f520ac3816de806f71232571. Public LF code equals qualified private code after CRLF normalization. The patch also records its qualified first-install default/test; original context is required, not arbitrary-upstream concatenation. CPUvision remains unchanged.

Fresh official main was fetched again and remains146df3c468739147f520ac3816de806f71232571. Settings: context262144/reserve150MiB/14workers/Q2 MTP/spec3/confidence.5/suffix3/PCIe1/q4_0 KVhost20480/CPUvision/standard xhigh. Author sampling:T1/top_p.95/top_k20/min_p0. Existing settings are never reset. Fresh Windows normal installation/UAC/task registration/full model download remain untested; Setup is unsigned.

The public native overlay was regenerated from its actual reviewed postimages on official146df3c, replacing the historicalffa80 overlay base. An independent Git index verified forward application on that exact base and reverse application on the actual public tree. The private compiled aggregate and runtime bytes did not change. Separately retained optional DS4 backend sources are not linked or bundled by this native-only release.
