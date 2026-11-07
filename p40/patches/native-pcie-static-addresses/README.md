# native-pcie-static-addresses

Builds stable PCIe staging addresses once and removes rebase_ptrs from each verification window. Requires the copy-overlap path.

Shared native CUDA verifier mechanism, without a model-name or quantization-specific dispatch. Separate GLM/DeepSeek engines do not automatically inherit this verifier code. Tested on P40; other models, operating systems and backends are not newly qualified here.

Status: already integrated in the published54828c7e/ef3d2944 engine. This publication separates existing deltas for review; it does not rebuild the engine or claim a new timing run. 51.65 to54.35tok/s in its original bounded Swift/P40 series (5.23% observed); accepted MTP tokens also changed48 to49, so the full difference is not attributed to pointer reuse. Percentages are not additive.

Original base tree: `187bcb47cc6f6859c09cc909a043b12483839a07`. Result tree: `0e628536864c28331154ae05e84aeff7225b03aa`. These are historical sequential patches, not drop-in replacements for an arbitrary fresh upstream tree. Adapt to current source and keep all stream/owner guards. `STRATA_PCIE_FETCH_OVERLAP=1` enables overlap; `STRATA_PCIE_STATIC_STAGE=1` additionally enables stable addresses where supported. Do not change model weights, selected experts, saved sampling or memory-residency policy.

Patch SHA256: `2f8e3d875178e7a54d8fc1e184686d1c454663415f139c5ba34e65fa9069e9be`. Native code retains the project's MIT license. The current integrated source and measured limits are in [Swift AVX1 PLE and retained patches](../../../docs/SWIFT_AVX1_PLE.md). No private configuration, weights or raw logs are included.
