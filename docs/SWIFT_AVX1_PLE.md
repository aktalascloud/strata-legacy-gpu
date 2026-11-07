# Swift: AVX1 PLE decode and fresh mainstream

Official Strata base: `54828c7efbcdf9474697e70922d851f6707f4b32`, engine 0.1.57. Native SHA256: `ef3d294498c5aa5295cbbe1427a83a3cfb549d6207bed96f0baf29a443adbd56`.

The new change replaces scalar IQ4_NL table lookups in `iq4nl_dequant_row` with 128-bit shuffle, signed extension, conversion and multiplication on AVX1 builds without AVX2. Swift's actual PLE tensor is IQ4_NL, width 160, and the RAM gather calls this function during generation. Codes, split-half order, F16 scales, weights and expert choices are unchanged. No AVX2, FMA, F16C, fast-math or GPU arithmetic is introduced. Other compile targets retain the scalar path.

Six alternating CPU timings, Ivy Bridge, strict FP:

| Working set | Scalar median ns/row | New median ns/row | Operator speedup |
| --- | --- | --- | --- |
| 16 rows | 162.885 | 51.8095 | 3.14 x |
| 16384 rows | 184.662 | 86.245 | 2.14 x |

262144 rows matched the original scalar function bit for bit: all 65536 F16 scale patterns, four unaligned offsets and output canaries. An additional 63488 finite rows matched the pinned independent GGML decoder. The linked production source matches the tested source apart from newlines. One CPU unit was rebuilt and the engine relinked; unchanged CUDA archives and CPUvision bytes reused their existing qualification. No new GPU numerical suite is claimed.

The live engine completed graceful schema3 shutdown/startup and four 64-token requests, with context 262144, reserve 150 MiB, 14 workers, PCIe 1, Q2 MTP+suffix, threshold 0.5, q4_0 KV with host20480 and CPU-only vision. Stored sampler/env settings stayed unchanged apart from executable/source paths. Author sampling and xhigh remain in the user's private config; no private config is bundled.

Whole-model A/B is inconclusive. Three warm old/new decode rates were 40.6/51.8/52.9 versus 42.7/43.7/47.2 tok/s. MTP acceptance differed (old 39/44/44, new 34/33/40), so work was not identical. These data establish neither a full-model gain nor a causal regression. The small exact CPU operator win is retained; no universal maximum or broad quality/perplexity claim.

The separate QSA Rows graph-bank experiment was rejected: the first 33K series improved 13.85%, but confirmation regressed 8.66%. It is not enabled in this engine. Earlier unqualified Q8/MTP experiments are not silently selected.

## Changes retained relative to stock

- AVX1/strict-FP and CUDA12.9/sm61 build support; native math selected for Pascal without Tensor Cores.
- RAM-residency guards for CPU experts, embeddings and PLE; CPU-only projector and model-specific capability guards.
- Guarded schema3 admission/drain and independent startup; API reasoning/model settings retain their reviewed behavior.
- Prior qualified PCIe/static staging and exact CPU improvements remain. Their historical gains are workload-specific and are not added to this operator percentage.
- PLE sanitizer and shard identity checks retained; optional Q2 bit-plane code remains off in the saved Swift profile.
- New exact PLE shuffle decoder above. Separate DeepSeek C20 public changes remain preserved in their own engine; no new DeepSeek runtime qualification is claimed.

## PR coverage

The remaining 5429 revisions in the frozen two-calendar-month snapshot have per-PR applicability decisions.1445 received code-applicability conclusions; the rest have explicit scope, already-present or superseded decisions. A final refresh read six additional PR diffs and twelve updated issue discussions across 81/82 tracked repositories (Strata-Lite unavailable). This is not a full semantic/security audit of every line. Exact HEADs are retained in the private review ledger to avoid repeating the work. Tool-call issue 4751 remains an unresolved upstream report; administrative closure of a report is not proof of a fix.

No model weights, logs, chat history, credentials, private settings, SDK or Microsoft runtime DLLs are distributed. The release is an engine overlay with explicit unchanged dependency hashes, not a complete portable installer. P 40/Ivy Bridge was tested; HIP/SYCL/other processors and a fresh Windows installation were not tested for this delta.

Кратко: ускорено точное CPU-декодирование PLE; исходные веса и выбор экспертов сохранены. Ускорение всей генерации пока не подтверждено. Контекст 262144, резерв 150 МиБ, Q2 MTP и CPUvision сохранены.
