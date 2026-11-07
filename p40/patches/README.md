# Separately reviewed patches

- [PCIe copy overlap](native-pcie-copy-overlap/README.md): overlap transfers and verification while keeping stream dependencies.
- [Stable PCIe staging addresses](native-pcie-static-addresses/README.md): remove repeated address rebasing from verification windows.
- [Exact AVX1 IQ4_NL PLE decode](avx1-ple-iq4nl-shuffle/README.md): one format-specific CPU improvement, separately labelled as operator-only.

The first two affect the shared native verifier and are not selected by a model name or quant type. Their historical model measurements are scoped to Swift/P40. No universal throughput claim or new other-model benchmark is made. Experimental candidates are published only with an explicit status; failed candidates are not silently enabled.

Experimental, not active:

- [Transposed native matvec](native-mmvq-transposed-reduction/README.md): numerical checks passed; no confirmed model speed benefit.
- [Vectorized table staging](cuda-staged-table-copy/README.md): isolated operation improvement; model A/B pending.
