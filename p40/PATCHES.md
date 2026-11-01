# Reviewed patches

`native-ivybridge-p40.patch` preserves the native AVX1/Pascal, API, no-pin, NUMA and lifetime fixes on the exact upstream revision.
`pascallama-sm61.patch` applies J96/unroll plus reviewed MMQ bounds/register extraction to the pinned GGML build copy. The dependency checkout stays unchanged.
`pillow13-security.patch` retains the qualified dependency fix. Keep original licenses and attribution.

The source/provenance manifests identify exact inputs. Do not apply a patch twice, replace newer files with old copies, or change a fingerprint to bypass review. `build-profile.json` is the qualified reference recipe. Keep ISA/SM/SRAM/FP guards. New mathematical bytes require applicable numerical checks; unchanged components require exact reuse evidence, not repeated sweeps.
