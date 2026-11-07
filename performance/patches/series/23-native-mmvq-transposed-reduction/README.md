# 23. native-mmvq-transposed-reduction

Статус: численно проверена; в основной профиль не включена — прирост генерации не подтверждён.

Status: **not_selected**. Historical experiment, rejected or not confirmed in the selected runtime. Original inputs and measured limits are retained; no activation implied.

Статус: численно проверена; в основной профиль не включена — прирост генерации не подтверждён.

База: main `54828c7efbcdf9474697e70922d851f6707f4b32`, активный aggregate `54828c7efbcd-b8a5c44a-ef3d2944-99e1cac7-d0bddbd7`. Отдельный патч: `change.patch`.

`STRATA_MMVQ_TSUM=1` совмещает имеющуюся транспонированную butterfly-редукцию S26 с повторным использованием фрагментов активаций B6. Старый `STRATA_TSUM` отключал B6, поэтому совместить эти пути было нельзя. Форматы без B6 используют существующую обычную транспонированную редукцию. Никакие веса, кванты, выбранные эксперты или арифметика dot-product не заменяются.

Это общий CUDA-механизм native matvec, без проверки имени модели или конкретного GGUF. Для тайлов больше 32 значений сохраняется прежняя B6-редукция; HIP не включается новым флагом. Старые режимы и выключенный новый флаг сохраняют прежний выбор пути.

Проверки фактической дельты прошли: 49152 lane outputs против независимой xor-butterfly; B6 rows2/4 против одиночных колонок, нечётные хвосты; Q8 direct/Graph по 65 случаев; BF16 off/on — 40 случаев без разницы битов. Проверка IQ дала ноль ошибок, но без EXPERT_V2 она не доказывает исполнение его TSUM-ветки: текущий EXPDEC её обходит. В A/B Swift/P40 изолированный вариант дал 37,8 против 39,5 ток/с контроля. В общей TSUM-серии 39,3 против 38,1, но относительно исходного контроля 38,8 выигрыш 1,29% меньше разброса MAD 1,53%; ускорение не подтверждено. Базовые параметры восстановлены. Для других моделей tok/s не заявлен. CUDA device math flags не менялись.

Patch SHA256: `446dcc267f382e84b1df21db27fca7ed1f8632afe7b15ca7883e4cacbf3b106c`. This is the original historical delta, with its own base/context.

Numbering gives stable catalogue IDs. Apply only an explicitly selected delta to its documented base; these historical patches overlap and include rejected experiments. The current published source is the integration reference. Measurements belong to their stated operation/model/source and are not additive.

Original third-party copyright and license statements in exported patches are retained. See [repository license](../../../../LICENSE) and [third-party notices](../../../../THIRD_PARTY_NOTICES.md).
