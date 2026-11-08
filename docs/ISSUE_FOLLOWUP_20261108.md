# Issue and source follow-up,8 November2026

The following are issue/discussion decisions, not new code patches or hardware reproductions.

| Source | Read scope and decision |
|---|---|
| [Niko1221/Strata/issues/5564](https://github.com/Niko1221/Strata/issues/5564) | Full body read,0 comments. Report is2x2080Ti/Linux/LXC/layer-split26/pipeline1, cancellation during111K prefill, subsequent stall. Root cause remains a hypothesis. Current oneP40/no-layer-split profile differs; health alone is insufficient, so our existing schema3 owner+loaded+actual API evidence is retained. No unused two-GPU or full262144 throughput test claimed, no watchdog/kill policy change. |
| [Niko1221/Strata/issues/4009](https://github.com/Niko1221/Strata/issues/4009) | Full body/all8 comments read. Last reporter follow-up says engine0.1.54 appeared to fix it. Reported0.1.48/50 HIP S1 symptoms and guessed mechanisms do not establish current0.1.58 CUDA corruption; per-layer expert caching stores weights, not prompt activations. Preserve strict token/checkpoint/image identity and current upstream guards. No forced cache deletion, weight redownload, repeated cache tests or unsupported model-ID bypass. |
| [Niko1221/Strata/issues/4053](https://github.com/Niko1221/Strata/issues/4053) | Full body/all2 comments read. SYCL/Intel xe dualB60 spin-bound ratchet; follow-up2M bound is25x80K, a single non-stationary zero-event run, not a proven rate or general remedy. Current CUDA/TCC/P40 path does not use that SYCL wait bound. Do not raise waits or import Intel scheduling settings; keep errors/finite checks and existing platform guards. No unused SYCL execution. |

Updated open-PR pages were refreshed for Strata/Maya/PolyStrata, and all-state recent pages for Xolotl/Delta/Abra/FreeToken. Those pages are inventory, not semantic review. PolyStrata currently resolves to simplexai-labs/PolyStrata. Abra#1/#2 and Delta#2 retain their previously reviewed exact heads; their unchanged code was not re-tested.

Previous requested-source reports retain their limits: glm-pascal-setup describes a different GLM/llama.cpp/32K prefill configuration; Abra uses Q4_K×Q8_1 and GPU-specific shape tables, with a previously tried native activation-reuse adaptation not selected; Bonsai2 uses a dense9B ternary/PQ2 model, unlike native Swift IQ3_S. Transferable launch/shape ideas are assessed on P40; unrelated model and GPU percentages are not assigned to Swift.

Current selected native/API patches remain54/55/56;30 retained source/workflow entries are not30 speedups. Full all-source semantic review remains open. These documents change no application, payload, native qualification or model settings; Setup r2 stays bound to its code merge.
