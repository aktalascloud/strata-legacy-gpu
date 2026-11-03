# Strata Legacy GPU

[English](README.md) · [Русский](README.ru.md) · [Windows ZIP](https://github.com/aktalascloud/strata-legacy-gpu/releases/latest)

Локальный OpenAI-совместимый сервер для Windows/Ivy Bridge/P40. Один пользовательский `strata.json`; модель выбирается данными и совместимым backend, а не названием приложения.

**Движок 0.1.56**, source `ffa80d73133e` (`ffa80d73133ea5c548aefe57889a16e8085a938f`). Квалифицирован профиль AVX1/Pascal sm61; ZIP содержит classic native E4 и отдельно проверенный CPU vision helper. DeepSeek/MiniMax и другие backend-исходники остаются experimental; непроверенные native runtime не включены.

1. Распакуйте ZIP, проверьте SHA256SUMS, запустите `INSTALL.cmd`.
2. Установите подготовленную native-модель; дополнительные generic backends в этом ZIP представлены только исходниками. Веса и личные настройки в ZIP не входят.
3. `START.cmd` запускает сервер; `CHECK.cmd` проверяет установку; `STOP.cmd` завершает её штатно. `AUTOSTART.cmd` включает независимый запуск.

API: `/v1/models`, `/v1/chat/completions`, `/v1/responses`, `/v1/messages`. Адрес и режимы задаются конфигурацией. Авторские Auto/Ultra не выдаются неподходящим моделям.

Сборка из исходников: VS2022 x64 Developer PowerShell, Clang23.1.4, CUDA12.9, CMake/Ninja/Git; команда `powershell -File p40/build.ps1 -Jobs 12`. CPU vision: `powershell -File p40/build-vision.ps1 -Jobs 12`, с проверяемым overlay в отдельной копии зависимости. Новая сборка не является квалификацией новых байтов.

[Исторические замеры](p40/BENCHMARKS.md) относятся к другой версии исходников/движка; ускорение текущей сборки пока не измерено.

[Изменения](p40/CHANGES.md) · [Рецепт](p40/build-profile.json) · [Проверки](p40/INSTALLATION-VERIFICATION.md) · [Лицензии](THIRD_PARTY_NOTICES.md) · [Оригинальный проект](https://github.com/Niko1221/Strata)
