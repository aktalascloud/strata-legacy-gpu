# Vectorized CUDA table staging

Experimental, **not enabled in the released engine**. Copies opaque 32-bit codebook words using aligned128/64-bit loads/stores, with scalar alignment/tail fallback. The shared IQ CUDA consumers use this helper; sign-mask construction, barriers, weights and floating point expressions stay unchanged. No model-name or one-quant dispatch is added; original HIP loops remain.

Fresh P40 prototype:72 constant/global, aligned/unaligned and output-bound checks passed. Six interleaved rounds, scalar/vector median9.367/6.300 microseconds (about32.7% lower time for this isolated operation). PTX contains vector constant loads and shared stores. This is **not a whole-model speed claim**. The real IQ consumer numerical qualification and Swift512-token A/B are still pending at this draft's creation. No binary is distributed here.

Base: upstream `54828c7efbcdf9474697e70922d851f6707f4b32` plus the published legacy aggregate, reconstructed tree `6db1359840eacdc4a900393f645553d45ccda4e8`. Adapt to the current tree before applying. Existing project MIT licensing is retained.

Patch SHA256: `671b8dc9204b230a446ca6067664496778ef4bc0b1758bd4d347b975ef451d40`.
