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

Windows, Tesla P40 24 GiB, два Xeon E5-2697 v2 (16 доступных ядер), 256 GiB RAM, CUDA 12.9. Каждый запрос Swift IQ3_S сгенерировал 768 токенов без чтения кэша. Варианты собирались отдельно на `c7757280` и запускались с одинаковым профилем.

Десктоп основан на upstream `v0.2.15`. Выбранный движок — `0.1.61` с CUDA `sm_61` и MMQ. Desktop is based on upstream `v0.2.15`; the selected engine is `0.1.61` with CUDA `sm_61` and MMQ.

| Движок / Engine | 9 292 + 768 | 24 368 + 768 |
|---|---:|---:|
| Сток / Stock, median of two controls | 48.39 s | 87.79 s |
| 01, AVX1 PLE | 48.21 s | 87.85 s |
| 57, route prior safety | 49.14 s | 87.88 s |
| 58, AVX1 FP16 scales | 49.52 s | 88.44 s |

Патчи 01, 57 и 58 исключены из активной сборки. На одном стоковом бинарнике `ADAPT_FETCH=2` снизил задержку на 16,7% и 2,3% по сравнению с `0`. Оставлены 14 воркеров. PLE Compact не дала повторяемого выигрыша.

The three individual patches produced no established end-to-end gain. On the same stock binary, `ADAPT_FETCH=2` reduced latency by 16.7% and 2.3% versus `0`. The selected pool has 14 workers. PLE Compact did not give a repeatable gain.

В Windows параллельный опрос CPU и GPU снизил медиану готовности App Host с 5,68 до 4,03 с в четырёх парных стартах. Поля железа совпали. Windows parallel probes cut median App Host readiness from 5.68 to 4.03 seconds in four paired starts, with identical hardware fields.

[Хеши, prefill, decode, ограничения измерений / Detailed results](legacy-p40/research/selection-20261118.json). [Предыдущий замер стока, форка и Setup / Earlier stock, fork and Setup comparison](legacy-p40/research/swift-desktop-ab-20261118.json).

На движке 0.1.61 запрос без чтения кэша с **261 998 входными и 128 выходными токенами** завершился без OOM за 913,43 с. Минимум свободной VRAM по выборке — 37 МиБ. `nvidia-smi` зарегистрировал температурное ограничение P40 при 89 °C.

On engine 0.1.61, a request with **261,998 input and 128 output tokens**, without a cache read, completed without OOM in 913.43 s. The sampled minimum free VRAM was 37 MiB. `nvidia-smi` reported P40 thermal slowdown at 89 °C.

На двух изображениях CPU Vision, 16 потоков, A/B/B/A: медианы повторов нового кодировщика примерно **3.27 с против 8.06 с** и **2.91 с против 7.27 с**. Выходы не побитово идентичны: cosine около 0.99985; реальные OCR-проверки `4217` и `STRATA 42` прошли. Это не гарантия качества на всех изображениях.

On two images, 16-thread CPU Vision A/B/B/A median encoding times were about **3.27 s vs 8.06 s** and **2.91 s vs 7.27 s**. Embeddings were not bit-identical (cosine about 0.99985); real OCR checks returned `4217` and `STRATA 42`. This does not establish quality for every image.

[Подробные данные и ограничения / Detailed evidence](legacy-p40/research/swift-20261118.json). PR #6124 и дополнительный общий AVX не показали устойчивого ускорения всей модели и не включены.

## Исходники / Source

Проект основан на [Niko1221/Strata](https://github.com/Niko1221/Strata), распространяется по условиям лицензий проекта и включённых компонентов. Для сборки нужны Windows SDK, MSVC, CUDA и Rust; модель и её Q2 MTP pack предоставляются пользователем отдельно.

Based on [Niko1221/Strata](https://github.com/Niko1221/Strata), subject to the project and bundled-component licenses. Building requires Windows SDK, MSVC, CUDA and Rust; the model and Q2 MTP pack are supplied separately.
