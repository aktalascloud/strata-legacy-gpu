# 28. pascal-qsa-rows-host-graph

Опциональный `STRATA_QSA_ROWS_AT` для одного sm_61 выбирает scorer по глубине окна. При смене режима дожидается CUDA stream и освобождает старый банк перед захватом следующего. Split, pipeline и `STRATA_SELECT_LONG` сохраняют своё поведение. Дополнительный scratch long top-k не выделяется.

Status: **not_selected**. Historical experiment, rejected or not confirmed in the selected runtime. Original inputs and measured limits are retained; no activation implied.

Опциональный `STRATA_QSA_ROWS_AT` для одного sm_61 выбирает scorer по глубине окна. При смене режима дожидается CUDA stream и освобождает старый банк перед захватом следующего. Split, pipeline и `STRATA_SELECT_LONG` сохраняют своё поведение. Дополнительный scratch long top-k не выделяется.

База `9f7d977d220e-b612b01b-6c0399ee-99e1cac7-d0bddbd7`. Scorer из [Strata #2059](https://github.com/Niko1221/Strata/pull/2059).

Проверка наложения и компиляция host-объекта прошли. Проверены переключения on/off и освобождение банков без OOM. Первая33K серия +13.85%, подтверждающая −8.66%; патч отклонён и в активный итоговый движок не входит. Доказательства swift-final-review-20261107/qsa-ab-* и qsa-confirm-*.

Patch SHA256: `6fd8af36ac3acd4e5d24ab37219935139e0f3de1d156e1f0b2f3f9323e13aece`. This is the original historical delta, with its own base/context.

Numbering gives stable catalogue IDs. Apply only an explicitly selected delta to its documented base; these historical patches overlap and include rejected experiments. The current published source is the integration reference. Measurements belong to their stated operation/model/source and are not additive.

Original third-party copyright and license statements in exported patches are retained. See [repository license](../../../../LICENSE) and [third-party notices](../../../../THIRD_PARTY_NOTICES.md).
