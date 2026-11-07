# Exact AVX1 IQ4_NL PLE decoding

Separate patch and CPU fixtures for the selected Swift change. See [measurements and limits](../../../docs/SWIFT_AVX1_PLE.md). Compile the production ngram.cpp and both fixtures as separate translation units with O3/Ivy Bridge AVX1, no AVX2/FMA/F16C or fast-math; link the normal strata_kernels, strata_core and ggml-base libraries. The checker calls the production decoder, the original scalar reference and the independent GGML trait. No model or GPU is used by this CPU fixture.
