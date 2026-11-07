# 01. avx1-ple-iq4nl-shuffle

Нативный `PleTable::gather_batch` вызывает `iq4nl_dequant_row` при генерации Swift. На AVX1 скалярные обращения к таблице заменены 128-битными shuffle, sign-extend, conversion и multiply. Остальные compile targets сохраняют прежний путь.

Status: **selected_source_or_dependency**. Retained in the selected source/runtime or dependency workflow. This catalogue does not reapply or rebuild unchanged bytes.

Нативный `PleTable::gather_batch` вызывает `iq4nl_dequant_row` при генерации Swift. На AVX1 скалярные обращения к таблице заменены 128-битными shuffle, sign-extend, conversion и multiply. Остальные compile targets сохраняют прежний путь.

Коды, split-half порядок, F16 scale и порядок умножения сохраняются. AVX2, FMA и F16C не используются. Ускорение операции в шести чередующихся прогонах — 3.14 раза для 16 строк и 2.14 раза для набора 16384 строк. Это CPU-оператор, не общий процент генерации.

Проверены 262144 строки против исходной скалярной функции, включая все 65536 значений F16 scale и невыравненные адреса. Различий битов 0, границы canary целы. Дополнительно 63488 строк совпали с независимым закреплённым GGML.


SHA патча `c7089c8eaa180a0eafef5a3b7a16eb0b6a03ec7d365b1c6c62bf87d3ade0ecec`.

Patch SHA256: `c7089c8eaa180a0eafef5a3b7a16eb0b6a03ec7d365b1c6c62bf87d3ade0ecec`. This is the original historical delta, with its own base/context.

Numbering gives stable catalogue IDs. Apply only an explicitly selected delta to its documented base; these historical patches overlap and include rejected experiments. The current published source is the integration reference. Measurements belong to their stated operation/model/source and are not additive.

Original third-party copyright and license statements in exported patches are retained. See [repository license](../../../../LICENSE) and [third-party notices](../../../../THIRD_PARTY_NOTICES.md).
