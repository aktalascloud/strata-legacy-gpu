# Strata Legacy GPU

[English](README.md) · [Русский](README.ru.md) · [Windows ZIP](https://github.com/aktalascloud/strata-legacy-gpu/releases/latest)

Локальный OpenAI-совместимый сервер для Windows/Ivy Bridge/P40. Один пользовательский `strata.json`; модель выбирается данными и совместимым backend, а не названием приложения.

**Движок 0.1.55**, source `c62d5e3a15b4` (`c62d5e3a15b40ea51c96aae9e8d36928965f53ab`). Квалифицирован профиль AVX1/Pascal sm61; остальные включённые backends имеют отдельные experimental-границы.

1. Распакуйте ZIP, проверьте SHA256SUMS, запустите `INSTALL.cmd`.
2. Выберите совместимый backend/локальную модель. Веса и личные настройки в ZIP не входят.
3. `START.cmd` запускает сервер; `CHECK.cmd` проверяет установку; `STOP.cmd` завершает её штатно. `AUTOSTART.cmd` включает независимый запуск.

API: `/v1/models`, `/v1/chat/completions`, `/v1/responses`, `/v1/messages`. Адрес и режимы задаются конфигурацией. Авторские Auto/Ultra не выдаются неподходящим моделям.

Сборка из исходников: VS2022 x64 Developer PowerShell, Clang23.1.4, CUDA12.9, CMake/Ninja/Git; команда `powershell -File p40/build.ps1 -Jobs 12`. Это сборка, не доказательство квалификации новых байтов.

[Последние замеры и их ограничения](p40/BENCHMARKS.md). Новый полный замер модели этой версии не выполнялся.

[Изменения](p40/CHANGES.md) · [Рецепт](p40/build-profile.json) · [Проверки](p40/INSTALLATION-VERIFICATION.md) · [Лицензии](THIRD_PARTY_NOTICES.md) · [Оригинальный проект](https://github.com/Niko1221/Strata)
