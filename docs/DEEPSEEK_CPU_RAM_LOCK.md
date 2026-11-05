# CPU-only locked expert memory on Windows / P40

The newer exact CPU row update is documented in [IQ2_XXS AVX1](DEEPSEEK_IQ2_AVX1.md). The memory placement and C17 measurements below remain their original evidence.

`STRATA_DS4_CPU_RAM_LOCK=1` keeps the CPU expert arena resident with Windows VirtualLock, instead of registering the whole arena with CUDA. CUDA registration can consume GPU mapping resources even when only the CPU reads those allocations. Cache swaps continue through their existing, separately pinned staging buffers. This is a memory-placement change, not new quantization, a changed expert-selection rule, or an approximation.

The public default is off. The qualified path requires Windows CUDA, one device, full private RAM copies, two ordinary NUMA parts, `--require-ram --mmap-experts off --prefill-chunk 0`, and no direct GPU streaming/zero-copy. Conflicting options fail closed. Every CPU arena page is checked as valid and locked; a failed lock prevents loading instead of falling back to the model files. Only this process's working-set quota is adjusted, following the existing Engram locking pattern. No privilege, system NUMA policy, affinity, power, driver, or unrelated service is changed. Readers are joined before unlock/free.

The retained CPU fixture checks 64 MiB / 16,384 pages, unchanged bytes, quota restoration, repeated calls and invalid/overlapping/overflowing extents. C16's GPU kernels and CPU expert arithmetic remain unchanged; their successful component evidence is reused rather than rerun or relabelled. Native INFO reports the actual arena lock bytes/pages and CUDA-registration state.

## Selected local result

Context262144, CPU12, reserve150MiB, Q2 MTP experts in RAM, confidence0.5, CPU-only projector, author temperature1/top_p1/high75. Original expert choices are retained. Actual GPU experts: 2041 (C16:2010). Full Engram and other generation weights remain resident. See the release result for the bounded decode samples; cache/shared-PC effects limit comparisons. No absolute maximum or universal quality-equivalence claim is made. Native CPU/GPU rounding continues to follow the framework's original behavior.

The full model lock, text generation and lowered-reserve headroom are distinct from the small CPU fixture. A 262144 context capacity is not a filled-context throughput test. Broad perplexity/semantic, multi-GPU, other backends, and fresh-Windows/full-portable acceptance are not newly qualified.

Recent upstream review: [Strata5199](https://github.com/Niko1221/Strata/issues/5199) describes prompt-buffer borrowing that displaces experts; this profile already uses chunk0/borrow0. [Strata5127](https://github.com/Niko1221/Strata/pull/5127) fixes an unused chunked-profiler path and is recorded separately. [Strata5256](https://github.com/Niko1221/Strata/pull/5256) needs separate adaptation for the external CPU projector; it is not included here. Source inventory is not a complete code review.
