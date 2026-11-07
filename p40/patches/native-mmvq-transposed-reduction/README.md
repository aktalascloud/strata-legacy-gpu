# Native matvec transposed reduction with activation reuse

Experimental, numerically qualified, **not enabled in the released engine**. Combines the existing S26 transposed butterfly with B6 activation reuse via `STRATA_MMVQ_TSUM=1`. Tiles wider than 32 outputs keep their original reduction; HIP is excluded. No model-name dispatch, new quantization or expert rerouting is introduced.

Fresh P40 checks: 49,152 lane outputs against an independent butterfly; B6 rows2/4 versus independent single columns including odd tails; Q8 direct and CUDA Graph, 65 cases each; BF16 off/on, 40 cases with identical bits. IQ regression checks passed, but the active EXPDEC path bypasses EXPERT_V2's TSUM branch; those checks do not demonstrate that V2 branch executing.

Swift/P40, identical 512-token request setup: isolated candidate median37.8 vs control39.5 tok/s. With the original TSUM enabled too:39.3 vs contemporary38.1, but just1.29% above the initial38.8 control, less than candidate MAD1.53%. No reliable model throughput gain was established; baseline settings were restored. Other models were not measured. Existing inherited CUDA math flags were unchanged.

Base: upstream `54828c7efbcdf9474697e70922d851f6707f4b32` plus the published legacy aggregate, reconstructed tree `6db1359840eacdc4a900393f645553d45ccda4e8`. Adapt to the current tree before applying. Existing project MIT licensing is retained.

Patch SHA256: `446dcc267f382e84b1df21db27fca7ed1f8632afe7b15ca7883e4cacbf3b106c`.
