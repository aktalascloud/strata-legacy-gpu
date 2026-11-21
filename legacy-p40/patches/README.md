# Активные патчи / Active patches

Индекс нативного движка фиксирует upstream `3142b66b`. Архив Desktop воспроизводит форк из `c7757280` с патчами в порядке номеров. The Desktop archive replays in number order onto `c7757280`. [Engine index](index.json)

- Нативный выбор папки Windows. Native Windows folder picker. [01](desktop/01-upstream-6185.patch)
- Русский интерфейс, трей, автокомпакт и FreeLLM. Russian UI, tray, automatic compaction and FreeLLM. [02](desktop/02-desktop-features.patch)
- Разбор файлов навыков. Skill file parsing. [03](desktop/03-skill-parser.patch)
- Автозагрузка Swift, LAN-помощники и медиашлюз. Swift autoload, LAN helpers and the media gateway. [04](desktop/04-swift-restart-and-providers.patch)
- Параллельный опрос CPU и GPU. Parallel Windows CPU and GPU probes. [05](desktop/05-windows-parallel-hardware.patch)
- Выключение reasoning для помощника KoboldCpp. Honor reasoning off for a KoboldCpp helper. [06](desktop/06-kobold-swarm-reasoning-off.patch)
- Проверка файлов цельной сборки движка. Verify monolithic engine files. [07](desktop/07-monolithic-engine-receipt.patch)
- Быстрая проверка отсутствия cloudflared при запуске. Faster startup when cloudflared is absent. [08](desktop/08-windows-cloudflared-preflight.patch)
