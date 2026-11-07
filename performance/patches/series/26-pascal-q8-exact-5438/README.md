# 26. pascal-q8-exact-5438

Источник [Strata #5438](https://github.com/Niko1221/Strata/pull/5438), HEAD `27ad9a02ac30382e35fe22528360fc4a8fc458aa`.

Status: **not_selected**. Historical experiment, rejected or not confirmed in the selected runtime. Original inputs and measured limits are retained; no activation implied.

Источник [Strata #5438](https://github.com/Niko1221/Strata/pull/5438), HEAD `27ad9a02ac30382e35fe22528360fc4a8fc458aa`.

CUDA12.9/sm61 сборка завершена. На P40 195 из 195 случаев совпали с native MMVQ побитово. Старое быстрое Q8 разошлось в 180 случаях. Экспертный Q2 pack не менялся.

В плотных весах текущего Swift нет Q8_0, поэтому эффект проверен с Q8-проекциями MTP. Лог подтвердил 9 из9 проекций, 68,7 МиБ дополнительных VRAM. Короткая серия дала 49,50 → 51,70 ток/с, после4K 37,95 → 39,45. Ответы и acceptance различались, разброс после4K превышал прирост. Подтверждённого ускорения модели нет. Выбран прежний Swift, исходный конфиг восстановлен штатно.


SHA-256 патча `10662ec9492ac72834137b3a160dd4641916d1c0f43aba4e8651a97765847892`.

Patch SHA256: `10662ec9492ac72834137b3a160dd4641916d1c0f43aba4e8651a97765847892`. This is the original historical delta, with its own base/context.

Numbering gives stable catalogue IDs. Apply only an explicitly selected delta to its documented base; these historical patches overlap and include rejected experiments. The current published source is the integration reference. Measurements belong to their stated operation/model/source and are not additive.

Original third-party copyright and license statements in exported patches are retained. See [repository license](../../../../LICENSE) and [third-party notices](../../../../THIRD_PARTY_NOTICES.md).
