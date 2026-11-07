# native-pcie-copy-overlap

Overlaps PCIe expert copies with independent verification work, retaining stream joins and the original expert arithmetic.

Shared native CUDA verifier mechanism, without a model-name or quantization-specific dispatch. Separate GLM/DeepSeek engines do not automatically inherit this verifier code. Tested on P40; other models, operating systems and backends are not newly qualified here.

Status: already integrated in the published54828c7e/ef3d2944 engine. This publication separates existing deltas for review; it does not rebuild the engine or claim a new timing run. 51.90 to52.55tok/s in its original bounded Swift/P40 series (1.25% observed). Percentages are not additive.

Original base tree: `aad36a459ec354b7858caa648c160cbe2a7adba0`. Result tree: `187bcb47cc6f6859c09cc909a043b12483839a07`. These are historical sequential patches, not drop-in replacements for an arbitrary fresh upstream tree. Adapt to current source and keep all stream/owner guards. `STRATA_PCIE_FETCH_OVERLAP=1` enables overlap; `STRATA_PCIE_STATIC_STAGE=1` additionally enables stable addresses where supported. Do not change model weights, selected experts, saved sampling or memory-residency policy.

Patch SHA256: `507f617c104c7baf9e016ec564e116990bf02e1297c4ada72266db308ed4a0fa`. Native code retains the project's MIT license. The current integrated source and measured limits are in [Swift AVX1 PLE and retained patches](../../../docs/SWIFT_AVX1_PLE.md). No private configuration, weights or raw logs are included.
