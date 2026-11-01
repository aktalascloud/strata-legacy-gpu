# Maintenance and publication

This fork retains the real Niko1221/Strata ancestry and original licenses. Use normal fetch/merge and push; never rewrite history, force-push, replace new upstream files with old snapshots, or delete published release tags/assets.

Review all configured sources, including the retained historical source list; prioritize [Strata](https://github.com/Niko1221/Strata), [Project Maya](https://github.com/mw00/project-maya) and [PolyStrata](https://github.com/VecSzn/PolyStrata). Track main/branches, PRs/issues and changed discussions. Metadata inventory, body screening and semantic code review are separate. Record accepted/rejected/deferred decisions and uncovered code; this tree does not claim exhaustive historical review. The three priority repositories do not replace the previously configured historical sources. Daily maintenance continues that backlog and includes new sources when explicitly configured.

Preserve the user's single strata.json, prepared model data and supported native modes. Build only an inactive tree with the pinned O3/Ivy AVX1/CUDA12.9/sm61/strict-FP recipe and at most12 total jobs. Keep background CPU use bounded; do not change affinity, system NUMA policy, hardware settings or unrelated services.

Validate the actual delta. Exact unchanged bytes reuse their source-bound receipts. Changed math/Graph/lifetime/ISA require applicable numerical checks; full DenseF32 never uses quick mode. Changed packaging/helpers need focused offline checks and privacy/integrity verification. No changes means no duplicate build, tests or restart. Retain every matched, useful improvement; compare the same workload/settings, account for background traffic and reject workload regressions of2% or more. Operator gains are not whole-model gains; percentages are not additive.

Never overwrite loaded binaries or their pinned source/checks. Switching requires exact owner/source/config/nonce/time, bounded idle, atomic graceful drain, a valid receipt, captured-tree completion and a free port. No kill/cancel. Verify loaded/API/settings/owner after startup. Rollback requires proven shutdown of the new owner; otherwise retain rollback_pending.

After a healthy deployment, remove obsolete local artifacts only after reference/process/absolute-path containment checks. Preserve required data, tools, licenses, active/locked files and policy-blocked targets. Ignored local files are not release content; never force-add them. Keep compact current conclusions and the unresolved backlog.

Publish only [aktalascloud/strata-legacy-gpu](https://github.com/aktalascloud/strata-legacy-gpu). Export an allowlist without weights/pack/MTP, private configuration/state/keys, hosts, conversations, raw logs, caches or toolchains. Keep licenses and true source/native provenance. Verify source and full runtime privacy, ZIP member CRC/SHA, then draft/upload ZIP+SHA and verify remote state/size/digest before publishing/readback. New package bytes require a new revision; GitHub failure leaves a healthy server running.

See [qualification scope](INSTALLATION-VERIFICATION.md), [current changes](CHANGES.md), [measurements and limits](BENCHMARKS.md), [patches](PATCHES.md) and [source provenance](source-provenance.json). Revision r2 reuses r1 native/runtime/helper bytes; its new material is documentation and sanitized results.
