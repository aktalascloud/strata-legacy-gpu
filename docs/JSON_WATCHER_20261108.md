# Retire the EOF watcher before final JSON delivery

Selected narrow adaptation of [Xolotl#107](https://github.com/Indras-Mirror/Xolotl/pull/107), ad9a64df6785b1efbe8cd8e6f7939084aaf3950e (MIT). A client may read the full non-streamed body and close before handler cleanup. A per-request lock now orders EOF classification against retiring that completed response. Real write failures still propagate to the existing handler; genuine early disconnects remain cancellable. Streaming behavior is unchanged.

Actual-method isolated harness reproduced a completed response being falsely cancelled in the original server. Fixed regression:1 CPU test/3 semantic cases passed (complete-body close, early EOF, write failure). AST outside the two reviewed method bodies is identical, including engine/control/admission/drain and sampling. One actual HTTP nonstream request returned200, nonempty content and stop, with unchanged live config. The public metrics endpoint did not expose a numeric disconnect counter; no counter claim is made. No live fault injection or GPU/benchmark repeat.

Native d8ee83c2, CPUvision and all non-serving source bytes were reused with their original qualification manifests/receipts, not relabelled as new tests. Local deployment was schema3 graceful/startup, loaded/API verified. Context262144/reserve150MiB/14workers/PCIe1/Q2 MTP/q4_0 KVhost20480/CPUvision/standard xhigh/author sampler/exact route0 retained. This is an API reliability fix, not a generation-TPS speedup. Previous exact0 model results remain scoped, noisy comparisons.

Native performance receipts remain the exact d8ee83c2 measurements in [singleton report](PASCAL_SINGLETON_CACHE_20261108.md). They were not rerun for this Python-only delta. Setup r2 contains the changed server/control-review payload; original r1 release bytes are immutable.

Additional review: Maya891 all3 diffs/body read; existing native request reasoning_budget_tokens/thinking_budget_tokens already cover the use case. Xolotl108 all2 diffs/body/current queue code read; current Strata already retains the original queue and has a different cancellation architecture, so its epoch/owner API cannot be copied directly. No unused batch-capture or GPU test claimed. Full source audit remains open.

Exact additional review heads: Xolotl107 `ad9a64df6785b1efbe8cd8e6f7939084aaf3950e`; Xolotl108 `4060b3561d690ba34ef6f0912eae866db4089bef`; Maya891 `8e3ed32119c8e6f26cd205eb740b1dfa863a5766`. This pass has13 PR records:10 complete changed-file scopes and3 explicitly bounded/partial scopes; this is not a global all-source percentage.
