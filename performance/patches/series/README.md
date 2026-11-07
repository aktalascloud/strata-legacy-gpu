# Numbered Strata patch catalogue

Each folder has its purpose, status, SHA256 and original patch when public source export is appropriate. Selected code, dependency overlays, optional modes, retired-model history and unselected experiments are labelled separately. Local deployment recipes are described with links to generic public counterparts; private configuration and task state are not exported.

The numbers are catalogue IDs. This history contains overlapping deltas and different bases. Use a patch only with its stated base and status; the current published source is the integration reference. No already-applied patch is applied again by this publication.

[Machine-readable index](index.json). Existing p40/patches links stay available for compatibility. [Recent P40 review and measurement limits](../../../docs/PASCAL_DECODE_REVIEW_20261107.md).

- [01. avx1-ple-iq4nl-shuffle](01-avx1-ple-iq4nl-shuffle/README.md) — `selected_source_or_dependency`
- [02. avx1-q2-bitplane-pair-4854](02-avx1-q2-bitplane-pair-4854/README.md) — `source_present_optional_off`
- [03. community-root-recipe-20261023](03-community-root-recipe-20261023/README.md) — `workspace_recipe_reference`
- [04. cpu-avx1-pr2638](04-cpu-avx1-pr2638/README.md) — `historical_input`
- [05. cpu-guided-build-recipe](05-cpu-guided-build-recipe/README.md) — `workspace_recipe_reference`
- [06. cpu-vision-on-demand-integration](06-cpu-vision-on-demand-integration/README.md) — `selected_source_or_dependency`
- [07. cuda-staged-table-copy](07-cuda-staged-table-copy/README.md) — `not_selected`
- [08. dense-f32-required-check](08-dense-f32-required-check/README.md) — `workspace_recipe_reference`
- [09. ggml-glm-cpu-vision-and-mtp](09-ggml-glm-cpu-vision-and-mtp/README.md) — `retained_optional_model_history`
- [10. immutable-build-work](10-immutable-build-work/README.md) — `workspace_recipe_reference`
- [11. independent-startup](11-independent-startup/README.md) — `workspace_recipe_reference`
- [12. ivy-o3-pascal-build](12-ivy-o3-pascal-build/README.md) — `workspace_recipe_reference`
- [13. lookup-4928-candidate](13-lookup-4928-candidate/README.md) — `not_selected`
- [14. minimax-maya-avx1-host](14-minimax-maya-avx1-host/README.md) — `retained_optional_model_history`
- [15. minimax-maya-avx1-sm61](15-minimax-maya-avx1-sm61/README.md) — `retained_optional_model_history`
- [16. minimax-native-integration](16-minimax-native-integration/README.md) — `retained_optional_model_history`
- [17. minimax-packer-integration](17-minimax-packer-integration/README.md) — `retained_optional_model_history`
- [18. minimax-serving-integration](18-minimax-serving-integration/README.md) — `retained_optional_model_history`
- [19. minimax-tokenizer-integration](19-minimax-tokenizer-integration/README.md) — `retained_optional_model_history`
- [20. minimax-unified-serving](20-minimax-unified-serving/README.md) — `retained_optional_model_history`
- [21. model-storage-root](21-model-storage-root/README.md) — `workspace_recipe_reference`
- [22. native-console-owner-control](22-native-console-owner-control/README.md) — `workspace_recipe_reference`
- [23. native-mmvq-transposed-reduction](23-native-mmvq-transposed-reduction/README.md) — `not_selected`
- [24. nvml-pcie-readings](24-nvml-pcie-readings/README.md) — `selected_source_or_dependency`
- [25. pascal-q4-attn32-4567](25-pascal-q4-attn32-4567/README.md) — `not_selected`
- [26. pascal-q8-exact-5438](26-pascal-q8-exact-5438/README.md) — `not_selected`
- [27. pascal-qsa-rows-context-gate](27-pascal-qsa-rows-context-gate/README.md) — `not_selected`
- [28. pascal-qsa-rows-host-graph](28-pascal-qsa-rows-host-graph/README.md) — `not_selected`
- [29. pascallama-sm61-e6a28bc](29-pascallama-sm61-e6a28bc/README.md) — `selected_build_local_dependency_overlay`
- [30. pgo-thinlto-numa-recipes](30-pgo-thinlto-numa-recipes/README.md) — `workspace_recipe_reference`
- [31. pillow13-security](31-pillow13-security/README.md) — `selected_source_or_dependency`
- [32. prefill-layer-major-scratch-5418](32-prefill-layer-major-scratch-5418/README.md) — `candidate_pending_or_upstream_superseded`
- [33. shared-settings-4934](33-shared-settings-4934/README.md) — `selected_source_or_dependency`
- [34. swift-iq4nl-avx1](34-swift-iq4nl-avx1/README.md) — `not_selected`
- [35. swift-pcie-copy-overlap](35-swift-pcie-copy-overlap/README.md) — `selected_source_or_dependency`
- [36. swift-pcie-fetch-stripes](36-swift-pcie-fetch-stripes/README.md) — `not_selected`
- [37. swift-pcie-static-addresses](37-swift-pcie-static-addresses/README.md) — `selected_source_or_dependency`
- [38. swift-ple-nonfinite-4688](38-swift-ple-nonfinite-4688/README.md) — `selected_source_or_dependency`
- [39. swift-ple-shard-identity-5326](39-swift-ple-shard-identity-5326/README.md) — `selected_source_or_dependency`
- [40. swift-q2-three-columns](40-swift-q2-three-columns/README.md) — `not_selected`
- [41. swift-q6-two-warps](41-swift-q6-two-warps/README.md) — `not_selected`
- [42. swift-qsa-q4](42-swift-qsa-q4/README.md) — `not_selected`
- [43. swift-shared-expert-q81-reuse](43-swift-shared-expert-q81-reuse/README.md) — `not_selected`
- [44. tool-buffer-chunks](44-tool-buffer-chunks/README.md) — `selected_source_or_dependency`
- [45. windows-numa-arena](45-windows-numa-arena/README.md) — `selected_source_or_dependency`
- [46. windows-preflight-json-bom](46-windows-preflight-json-bom/README.md) — `workspace_recipe_reference`
