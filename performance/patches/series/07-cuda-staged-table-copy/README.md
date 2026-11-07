# 07. cuda-staged-table-copy

Статус: кандидат собран и численно проверен; в основной движок не выбран. Подтверждённый прирост генерации не заявлен. Патч опубликован отдельно в aktalascloud/strata-legacy-gpu PR #8.

Status: **not_selected**. Historical experiment, rejected or not confirmed in the selected runtime. Original inputs and measured limits are retained; no activation implied.

Статус: кандидат собран и численно проверен; в основной движок не выбран. Подтверждённый прирост генерации не заявлен. Патч опубликован отдельно в aktalascloud/strata-legacy-gpu PR #8.

База: свежий main `54828c7efbcdf9474697e70922d851f6707f4b32` и сохранённый aggregate активного Swift/ef3d2944. Патч добавляет `staged_table_copy.cuh` и меняет копирование таблиц в stage_iq_grid/EdGrid. Построение sign masks и барьеры сохранены.

Для выровненных таблиц копирует 128 или 64 бита за операцию; при неподходящем выравнивании или хвосте сохраняет скалярный путь. Не меняет содержимое таблиц, веса, кванты или арифметику модели. Механизм не проверяет имя модели/формат GGUF. HIP не включается новым CUDA-путём.

GPU-прототип CUDA12.9/sm61 прошёл 72 проверки constant/global, выровненных/невыровненных адресов и границ. В PTX подтверждены `ld.const.v4.u32`/`st.shared.v4.u32`. Шесть чередующихся раундов на P40 для таблицы 1024 слова в constant memory: медианы скалярного/векторного копирования 9,367/6,300 мкс (время меньше примерно на 32,7%). Это отдельная операция, а не ускорение всей модели; реальные IQ-таблицы используют device memory. Их проверки IQ MMVQ/grouped и EXPDEC с grid0/grid1 прошли без расхождений, модельный A/B завершён; итог приведён ниже.

Две пары модельного A/B по 512 токенов: кандидат `[38.0,38.4,38.3,39.1,38.2,38.0,38.7,39.0]`, контроль `[37.8,37.8,37.9,38.4,37.7,37.0,37.6,37.8]` ток/с. Наблюдаемый выигрыш медиан 1,455%, максимальный MAD 0,910%; порог уверенного выбора 1,821% не пройден. Приём MTP тоже различался. Исходный профиль восстановлен; результат не назван подтверждённым ускорением генерации.

Patch SHA256: `671b8dc9204b230a446ca6067664496778ef4bc0b1758bd4d347b975ef451d40`. This is the original historical delta, with its own base/context.

Numbering gives stable catalogue IDs. Apply only an explicitly selected delta to its documented base; these historical patches overlap and include rejected experiments. The current published source is the integration reference. Measurements belong to their stated operation/model/source and are not additive.

Original third-party copyright and license statements in exported patches are retained. See [repository license](../../../../LICENSE) and [third-party notices](../../../../THIRD_PARTY_NOTICES.md).
