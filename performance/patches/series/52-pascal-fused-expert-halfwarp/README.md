# Exact fused expert half-warps on Pascal

Selected in the main Swift profile and first-install preset with STRATA_SM61_FUSED_H2=1. Adapted from Niko1221/Strata#5033 at06d119bce57539b70b717b187f0e03049e95dbac (MIT), to the used mode8 fused GU/SwiGLU/Q8 path. The PR's separate mode7 flag alone would not reach this path.

Each physical half-warp carries two original logical lanes independently and replays XOR16/8/4/2/1. Weights, router choices, dot products, nonlinear epilogue and quantization remain unchanged. Guard: sm61/experimentalCUDA, auto mode8, GU21/down20or42,2560x640, nonstrided capacity10/20/30/40. Manual modes, old/v1, Hadamard, nibble and other GPUs retain the old path. Default remains off outside the qualified preset.

Detached240 direct/Graph cases match raw prequantization values and Q8 bytes; reference Q8 matches the actual preceding6c51 archive. Six alternating Graph timing rounds over rotating weight blobs show GU throughput+10.8..13.2%. Actual final native8cc3edf0 passed56 layout/T/grid pairs direct/Graph,130 Q8 checks (one expected shared-memory decline per mode), and27 required package cases including fullF32. Operation percentages are not whole-model gains or additive with previous patches.

Same-native Swift off/on, two warmups plus five512-token measurements per arm: medians39.3/39.1tok/s, observed-0.51%, MAD1.27/0.26%, CPU7.3/7.3%. Identical text/draft work:False. Established whole-model TPS gain:False. Selection retains a confirmed exact operation gain absent a credible model regression. This is not an absolute maximum or a broad quality evaluation.

Base public revision9b5c9057ed256363d670c0a2e6c50f97d8207fb4, official source146df3c468739147f520ac3816de806f71232571. Public LF code equals qualified private code after CRLF normalization. The patch also records its qualified first-install default/test; original context is required, not arbitrary-upstream concatenation. CPUvision remains unchanged.
