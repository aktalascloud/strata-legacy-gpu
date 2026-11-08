# Strata Legacy GPU

[English](README.md) · [Русский](README.ru.md) · [Windows ZIP](https://github.com/aktalascloud/strata-legacy-gpu/releases/latest)

Локальный OpenAI-совместимый сервер для Windows/Ivy Bridge/P40. Один пользовательский `strata.json`; модель выбирается данными и совместимым backend, а не названием приложения.

**Движок 0.1.58**, официальный source `146df3c46873`, native `d8ee83c2`. [Полный Setup.exe и portable ZIP](https://github.com/aktalascloud/strata-legacy-gpu/releases/tag/v0.1.58-swift-p40-d8ee83c2-setup-r2) включают Python, P40 engine, CPU vision и WebUI. При первом запуске готовится Swift IQ3_S с совместимым Q2 MTP; веса, личные настройки и SDK не включены. [Патч, замеры и границы review](docs/PASCAL_FUSED_H2_20261108.md).

Новое в d8ee83c2: точное singleton-планирование GU (операция +4,45–11,13%) и атомарная публикация кэша при отказе выделения памяти (5 нарушений до,0 после). Swift без пропуска экспертов: greedy29,6/29,3ток/с; авторский T1 27,9/28,5ток/с. Различия в пределах разброса при разном принятии MTP; общий TPS-прирост не доказан. AVX1/P40, RAM/CPUvision, API и надёжность описаны в [30 отдельных source/workflow-патчах](performance/patches/series/README.md); это не30 ускорений. Прежние rank1 замеры использовали приближённый пропуск экспертов и остаются историческими.

1. Проверьте SHA256SUMS и запустите Setup.exe в новую папку либо распакуйте ZIP и запустите `INSTALL.cmd`.
2. Укажите папку Swift. Недостающие закреплённые файлы загружаются с докачкой. Setup сохраняет существующие config/runtime; рабочую установку обновляет её штатный updater.
3. `START.cmd` запускает сервер; `CHECK.cmd` проверяет установку; `STOP.cmd` завершает её штатно. `AUTOSTART.cmd` включает независимый запуск.

API: `/v1/models`, `/v1/chat/completions`, `/v1/responses`, `/v1/messages`. Адрес и режимы задаются конфигурацией. Авторские Auto/Ultra не выдаются неподходящим моделям.

Сборка из исходников: VS2022 x64 Developer PowerShell, Clang23.1.4, CUDA12.9, CMake/Ninja/Git; команда `powershell -File p40/build.ps1 -Jobs 12`. CPU vision: `powershell -File p40/build-vision.ps1 -Jobs 12`, с проверяемым overlay в отдельной копии зависимости. Новая сборка не является квалификацией новых байтов.

[Исторические замеры](p40/BENCHMARKS.md) относятся к прежним версиям. Выбранные dense-операции ускорились примерно на 6–40%; Swift 37,8 против 37,6 ток/с — ниже шума, общий прирост TPS не подтверждён. Извлечение, хеши и импорты Setup проверены; чистая Windows не проверялась. EXE не подписан.

[Изменения](p40/CHANGES.md) · [Рецепт](p40/build-profile.json) · [Проверки](p40/INSTALLATION-VERIFICATION.md) · [Лицензии](THIRD_PARTY_NOTICES.md) · [Оригинальный проект](https://github.com/Niko1221/Strata)

[Expert dispatch patch and measurements](docs/PASCAL_EXPERT_TABLE_20261107.md) · [Follow-up PR dispositions](docs/REVIEW_FOLLOWUP_20261107.md).

[Exact fused experts and graph memory](docs/PASCAL_FUSED_H2_20261108.md) · [Latest PR review](docs/REVIEW_FOLLOWUP_20261108.md).

[Новые точные замеры и исправление кэша](docs/PASCAL_SINGLETON_CACHE_20261108.md) · [Новый разбор PR](docs/REVIEW_SINGLETON_CACHE_20261108.md). Прежние частные rank1 замеры — исторические приближённые результаты; текущий локальный и публичный профиль используют rank0.

[JSON completion fix and reused native qualification](docs/JSON_WATCHER_20261108.md). Native/model settings unchanged; no new speed claim.
