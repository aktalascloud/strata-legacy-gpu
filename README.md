# Strata Desktop · Legacy GPU

Русскоязычный форк Strata Desktop для Windows x64, Tesla P40 и процессоров с AVX1. Работает локально со Swift 1.5 Flash Next IQ3_S; модели в репозиторий и установщик не входят.

An independent Strata Desktop fork for Windows x64, Tesla P40 and AVX1 CPUs. Runs Swift 1.5 Flash Next IQ3_S locally; model weights are not included.

## Возможности / Features

- Desktop самостоятельно управляет локальным движком и OpenAI-совместимым API; предусмотрены автозапуск и защита от двух процессов модели.
- Desktop owns the local engine and OpenAI-compatible API, with startup integration and protection against duplicate model processes.
- Профиль Swift: CUDA `sm_61`, MMQ, контекст 256K, Q4 KV, Q2 MTP, prefill 1536, 14 CPU-воркеров и Vision на CPU в 16 потоков. Настраиваемый резерв установлен на 210 МиБ; фактически свободная VRAM может отличаться.
- Swift profile: CUDA `sm_61`, MMQ, 256K context, Q4 KV, Q2 MTP, prefill 1536, 14 CPU workers and 16-thread CPU Vision. The configured reserve is 210 MiB; actual free VRAM can differ.
- Русский интерфейс, отображение reasoning, Ponytail и настройки автокомпакта агентских чатов. Обычный чат и ручной `/compact` используют отдельное штатное поведение.
- Russian interface, reasoning display, Ponytail and configurable agent-chat compaction. Plain chat and manual `/compact` retain their own upstream behavior.
- FreeLLM через Kilo: Nemotron 3 Ultra 550B и Dots3-Note Preview 280B без ключа, с лимитами из API. Облако используется только после выбора модели; провайдер может использовать запросы для обучения.
- FreeLLM through Kilo: keyless Nemotron 3 Ultra 550B and Dots3-Note Preview 280B, with limits discovered from the API. Cloud use requires model selection; the provider may use prompts for training.
- Для роя выберите помощников в меню субагентов одного чата. Swift составляет текстовые подзадачи и собирает ответы. Поддерживаются сохранённые FreeLLM и KoboldCpp в локальной сети. История и вложения обрабатываются локально.
- Choose swarm helpers from a chat’s subagent menu. Swift drafts text subtasks and combines the answers. Saved FreeLLM and LAN KoboldCpp models can join. Chat history and attachments stay with the local orchestrator.
- В настройках можно сохранить медиашлюз KoboldCpp в локальной сети. Strata проверяет доступные функции, открывает Media Studio шлюза и отправляет генерацию звуковых эффектов по явной команде.
- Save a LAN KoboldCpp media gateway in Settings. Strata checks available features, opens the gateway’s Media Studio, and submits sound-effect requests when asked.

## Замеры / Measurements

Windows, Tesla P40 24 GiB, два Xeon E5-2697 v2 (16 доступных ядер), 256 GiB RAM, CUDA 12.9, Swift IQ3_S с Q2 MTP. Чистые запросы с 768 выходными токенами; показатели зависят от нагрузки и принятия MTP.

| Вход / Input | Prefill | Генерация / Decode | Полное время / Total |
|---|---:|---:|---:|
| 9 292 токена, контроль | 367.0 tok/s | 30.4 tok/s | 50.62 s |
| 24 368 токенов, контроль | 344.6 tok/s | 32.5 tok/s | 94.39 s |

Повторное сравнение stock и fork использовало одинаковые AVX1, CUDA 12.9, `sm_61` и MMQ. Каждый запрос сгенерировал 768 токенов без чтения кэша.

| Вход / Input | Stock, ABBA median | Fork, ABBA median | Setup engine |
|---|---:|---:|---:|
| 9 292 | 49.61 s | 49.49 s | 49.11 s |
| 24 368 | 88.63 s | 88.39 s | 88.39 s |

Устойчивый выигрыш патчей в полной задержке не подтвердился. [Хеши, NUMA, VRAM, prefill и decode / Detailed comparison](legacy-p40/research/swift-desktop-ab-20261118.json).

Один запрос без чтения кэша с **262 013 входными и 123 выходными токенами** завершился без OOM за 927,5 с. Минимум свободной VRAM по выборке — 37 МиБ; это результат конкретного теста, а не гарантия для любых задач.

One request with **262,013 input and 123 output tokens**, without a cache read, completed without OOM in 927.5 s. The sampled minimum free VRAM was 37 MiB; this is one workload, not a guarantee for every request.

На двух изображениях CPU Vision, 16 потоков, A/B/B/A: медианы повторов нового кодировщика примерно **3.27 с против 8.06 с** и **2.91 с против 7.27 с**. Выходы не побитово идентичны: cosine около 0.99985; реальные OCR-проверки `4217` и `STRATA 42` прошли. Это не гарантия качества на всех изображениях.

On two images, 16-thread CPU Vision A/B/B/A median encoding times were about **3.27 s vs 8.06 s** and **2.91 s vs 7.27 s**. Embeddings were not bit-identical (cosine about 0.99985); real OCR checks returned `4217` and `STRATA 42`. This does not establish quality for every image.

[Подробные данные и ограничения / Detailed evidence](legacy-p40/research/swift-20261118.json). PR #6124 и дополнительный общий AVX не показали устойчивого ускорения всей модели и не включены.

## Исходники / Source

Проект основан на [Niko1221/Strata](https://github.com/Niko1221/Strata), распространяется по условиям лицензий проекта и включённых компонентов. Для сборки нужны Windows SDK, MSVC, CUDA и Rust; модель и её Q2 MTP pack предоставляются пользователем отдельно.

Based on [Niko1221/Strata](https://github.com/Niko1221/Strata), subject to the project and bundled-component licenses. Building requires Windows SDK, MSVC, CUDA and Rust; the model and Q2 MTP pack are supplied separately.
