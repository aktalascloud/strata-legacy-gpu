# 32. prefill-layer-major-scratch-5418

Порт [Strata #5418](https://github.com/Niko1221/Strata/pull/5418) с HEAD `b62139404106ef7edf599cf7e5d094369f766757`.

Status: **candidate_pending_or_upstream_superseded**. Originally a pending source adaptation. Check the current mainstream postimage before applying; no standalone activation is claimed.

Порт [Strata #5418](https://github.com/Niko1221/Strata/pull/5418) с HEAD `b62139404106ef7edf599cf7e5d094369f766757`.

Считает предел строк группы из `group_cap` в планировании scratch и при разбиении экспертов. При выключенном group scratch обе ветки сохраняют прежний размер. Обработка decode и веса модели не меняются.

Проверено применение двух hunks через `git apply --check --whitespace=error-all` к `src/prefill/prefill.cpp`, файл совпадает с активной копией. SHA-256 файла базы `33d362cd9ae3511257e74c5ff85867962e04efedf080ce7d47510c462e9a0fa0`.

Кандидат для отдельной сборки и проверки длинного промпта. В агрегат ещё не включён.

SHA-256 патча `4b54925d3cc966c661dce394feb314937cbaee08dd442416558452f8aee4a5ae`.

Patch SHA256: `4b54925d3cc966c661dce394feb314937cbaee08dd442416558452f8aee4a5ae`. This is the original historical delta, with its own base/context.

Numbering gives stable catalogue IDs. Apply only an explicitly selected delta to its documented base; these historical patches overlap and include rejected experiments. The current published source is the integration reference. Measurements belong to their stated operation/model/source and are not additive.

Original third-party copyright and license statements in exported patches are retained. See [repository license](../../../../LICENSE) and [third-party notices](../../../../THIRD_PARTY_NOTICES.md).
