# Keep the long lookup without CUDA Graph churn

Selected first-install Swift preset adds --lookup-sizes4,12. MTP/spec3 retains sizes1/2/3; lookups retain4and12. The competing intermediate size5 is omitted. Context262144, reserve150MiB,9249 expert slots, weights and sampler remain unchanged. Existing user configuration is preserved.

On predecessor native6c51, the same512-token series recorded0 graph reclaims versus21 without this mask; median39.0tok/s versus38.6 was within noise. A23999-token cold/cached memory probe completed at42.8/47.3decode tok/s with0reclaims. These are explicitly predecessor/profile receipts, not new-native long-context timings or a full262144 throughput test. Current same-native H2 probe retains this graph set and its zero-reclaim selection gate.

KVhost20480 means cells per QSA layer, with the full KV copy in pinned RAM. Host streaming uses a fixed VRAM pool; --kv-grow is ineligible with positive kv_resident. No global CUDA loading mode, memory reserve, driver or OS policy is changed. Factory defaults only; no second user configuration is introduced.
