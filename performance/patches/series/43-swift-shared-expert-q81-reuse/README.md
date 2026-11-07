# 43. swift-shared-expert-q81-reuse

Идея Abra: общий эксперт читает готовые Q8_1 данные после события CUDA. Слои, которые перезаписывают буфер из-за Hadamard, сохраняют отдельную квантизацию.

Status: **not_selected**. Historical experiment, rejected or not confirmed in the selected runtime. Original inputs and measured limits are retained; no activation implied.

Идея Abra: общий эксперт читает готовые Q8_1 данные после события CUDA. Слои, которые перезаписывают буфер из-за Hadamard, сохраняют отдельную квантизацию.

Статус: Не выбран: 52,20 → 52,05 ток/с при разбросе 0,77%, различается принятие MTP. Прежний Swift восстановлен.

База: Дерево `4ee23a585d5a97c55def0591ec096dfe9b38c823`; результат `27d431c5eb921ab50c8e06a83870dbf2ff326856`.


SHA-256: `f41b9bb31e209b0a2c54ef9a614c705b2784447aa37eba3b3b7d75514c31dad6`.

Patch SHA256: `f41b9bb31e209b0a2c54ef9a614c705b2784447aa37eba3b3b7d75514c31dad6`. This is the original historical delta, with its own base/context.

Numbering gives stable catalogue IDs. Apply only an explicitly selected delta to its documented base; these historical patches overlap and include rejected experiments. The current published source is the integration reference. Measurements belong to their stated operation/model/source and are not additive.

Original third-party copyright and license statements in exported patches are retained. See [repository license](../../../../LICENSE) and [third-party notices](../../../../THIRD_PARTY_NOTICES.md).
