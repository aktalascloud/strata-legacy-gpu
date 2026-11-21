# Strata Desktop for Tesla P40

[Русский](#русский) · [Release / Скачать](https://github.com/aktalascloud/strata-legacy-gpu/releases/tag/v0.2.15-p40-r4) · [Patches / Патчи](legacy-p40/patches/) · [Evidence / Данные](legacy-p40/research/selection-20261118.json) · [Upstream](https://github.com/Niko1221/Strata)

Run Swift 1.5 Flash Next locally on Windows with a Tesla P40 and an Ivy Bridge AVX1 CPU. Strata manages the CUDA backend, exposes an OpenAI-compatible API and can connect to a KoboldCpp media gateway on your LAN.

**Quick start.** Use the Windows installer with your Swift IQ3_S GGUF files. The optional Q2 MTP pack is a separate download. The NVIDIA driver, Edge WebView2 and VC++ x64 Runtime are required.

**Evidence.** On engine `0.1.61`, one Swift IQ3_S request on P40 produced 128 tokens from a 261,998-token prompt in 913.43 s without a cache read. On the same system, four paired startup tests took a median 5.68 → 4.03 s for App Host readiness.

## Русский

Запускайте Swift 1.5 Flash Next локально на Windows с Tesla P40 и процессором Ivy Bridge AVX1. Strata управляет движком CUDA, предоставляет OpenAI-совместимый API и подключается к медиашлюзу KoboldCpp в локальной сети.

**Запуск.** Установите сборку Windows и укажите свои файлы Swift IQ3_S GGUF. Дополнительный пакет Q2 MTP загружается отдельно. Нужны драйвер NVIDIA, Edge WebView2 и VC++ x64 Runtime.

**Проверка.** На движке `0.1.61` одна сессия Swift IQ3_S на P40 обработала 261 998 входных токенов и выдала 128 токенов за 913,43 с без чтения кэша. В четырёх парных стартах медиана готовности App Host составила 5,68 → 4,03 с.

## Возможности / Features

- Desktop самостоятельно управляет локальным движком и OpenAI-совместимым API; предусмотрены автозапуск и защита от двух процессов модели.
- Desktop owns the local engine and OpenAI-compatible API, with startup integration and protection against duplicate model processes.
- Профиль Swift использует CUDA `sm_61`, контекст 256K, Q4 KV, Q2 MTP, prefill 1536, 14 CPU-воркеров и Vision на CPU в 16 потоков. Настраиваемый резерв составляет 210 МиБ.
- The Swift profile uses CUDA `sm_61`, a 256K context, Q4 KV, Q2 MTP, prefill 1536, 14 CPU workers and 16-thread CPU Vision. The configured reserve is 210 MiB.
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

Setup r4 включает Desktop `0.2.15` и движок `0.1.61` с CUDA `sm_61` и MMQ. В рабочей установке проверена `0.1.63` из `3142b66b` с CUDA 12.9 и AVX1. Setup r4 bundles Desktop `0.2.15` and engine `0.1.61` with CUDA `sm_61` and MMQ. The working installation was qualified with engine `0.1.63` from `3142b66b`, built with CUDA 12.9 and AVX1. [Upstream](https://github.com/Niko1221/Strata/commit/3142b66b96e9c0e775e30f620b11b191a1427c2a)

| Движок / Engine | 9 292 + 768 | 24 368 + 768 |
|---|---:|---:|
| Сток / Stock, median of two controls | 48.39 s | 87.79 s |
| 01, AVX1 PLE | 48.21 s | 87.85 s |
| 57, route prior safety | 49.14 s | 87.88 s |
| 58, AVX1 FP16 scales | 49.52 s | 88.44 s |

Патчи 01, 57 и 58 исключены из активной сборки. На одном стоковом бинарнике `ADAPT_FETCH=2` снизил задержку на 16,7% и 2,3% по сравнению с `0`. Оставлены 14 воркеров. PLE Compact не дала повторяемого выигрыша.

The three individual patches produced no established end-to-end gain. On the same stock binary, `ADAPT_FETCH=2` reduced latency by 16.7% and 2.3% versus `0`. The selected pool has 14 workers. PLE Compact did not give a repeatable gain.

В Windows параллельный опрос CPU и GPU снизил медиану готовности App Host с 5,68 до 4,03 с в четырёх парных стартах. Поля железа совпали. Windows parallel probes cut median App Host readiness from 5.68 to 4.03 seconds in four paired starts, with identical hardware fields.

На одинаковых 9 292 входных и 768 выходных токенах без чтения кэша Strata завершила запрос за **48,42 с**, официальный llama.cpp `b12503` — за **181,97 с**. llama.cpp работала с контекстом 256K, CUDA 12.4, CPU MoE и GPU-кэшем экспертов 12 000 МиБ, без MTP.

For the same 9,292 input and 768 output tokens with no prompt cache reads, Strata took **48.42 s** and official llama.cpp `b12503` took **181.97 s**. The llama.cpp run used a 256K context, CUDA 12.4, CPU MoE and a 12,000 MiB GPU expert cache, with MTP disabled.

Повторная серия из 20 запросов сравнила CUDA side mixer, адаптивный MTP, CPU-ядра ggml, 32K резидентного KV, CPU-пул, предзагрузку PLE, K8/V4, группировку экспертов и долю PCIe. Сохранили стоковый движок с проверенным профилем Q4 KV и Q2 MTP.

A 20-request follow-up compared CUDA side mixing, adaptive MTP, ggml CPU quant, 32K resident KV, CPU pool sizing, PLE prefetch, K8/V4, grouped experts and the PCIe fraction. The selected build remains stock with the qualified Q4 KV and Q2 MTP profile.

[Хеши, prefill, decode и ограничения измерений / Detailed results](legacy-p40/research/selection-20261118.json). [Предыдущие замеры стока, форка, MMQ, Vision и Setup / Earlier measurements](https://github.com/aktalascloud/strata-legacy-gpu/tree/18f4ae56b074c39e6ff0c93e2458b47ced4857bc/legacy-p40/research).

На движке 0.1.61 запрос без чтения кэша с **261 998 входными и 128 выходными токенами** завершился без OOM за 913,43 с. Минимум свободной VRAM по выборке — 37 МиБ. `nvidia-smi` зарегистрировал температурное ограничение P40 при 89 °C.

On engine 0.1.61, a request with **261,998 input and 128 output tokens**, without a cache read, completed without OOM in 913.43 s. The sampled minimum free VRAM was 37 MiB. `nvidia-smi` reported P40 thermal slowdown at 89 °C.

19 ноября `0.1.62` завершила запросы 9 292 и 24 368 + 768 токенов за **48,59 и 87,97 с**. Оба результата находятся внутри диапазона двух контролей `0.1.61`. Чанк 2048 и QFUSE не дали устойчивого прироста. В паре на 96K длинный селектор QSA прошёл за 318,47 с при базовых 311,17 с и более тёплом старте. Запрос 261 998 + 128 занял **908,61 с** без OOM. Минимум свободной VRAM по выборке составил 27 МиБ.

On November 19, `0.1.62` completed the 9,292 and 24,368 + 768 token requests in **48.59 and 87.97 s**, within the two `0.1.61` controls. A prefill chunk of 2048 and QFUSE gave no consistent gain. The 96K long-selector run took 318.47 s versus 311.17 s and started warmer. The 261,998 + 128 token request took **908.61 s** without an OOM. Sampled free VRAM reached 27 MiB.

На `0.1.63` после десяти коротких запросов порог `--conversation-cache-min-tokens 2048` сохранил 9 285 из 9 292 токенов длинного запроса. Повтор занял **1,70 с** против **24,72–24,91 с** в двух штатных контролях. Порог применяется к парковке диалогов. [Сценарий upstream](https://github.com/Niko1221/Strata/issues/6463)

On `0.1.63`, `--conversation-cache-min-tokens 2048` preserved 9,285 of the long prompt's 9,292 tokens after ten short requests. The return took **1.70 s** versus **24.72–24.91 s** in two stock controls. The threshold applies to parked conversations. [Upstream scenario](https://github.com/Niko1221/Strata/issues/6463)

Холодные запросы на 9 292 и 24 368 входных токенов заняли **48,92 и 87,74 с** на штатной `0.1.63`. Расширение CPU-доли до 16 токенов на эксперта и предзагрузка L2 с лимитом 2 МиБ замедлили оба запроса. С порогом 2048 запрос на 261 998 + 128 токенов прошёл без OOM за **906,99 с**. Минимум свободной VRAM по выборке составил 29 МиБ.

Cold requests with 9,292 and 24,368 input tokens took **48.92 and 87.74 s** on stock `0.1.63`. The wider CPU share and the 2 MiB L2 prefetch slowed both requests. With the 2048-token threshold, the 261,998 + 128 token request completed without OOM in **906.99 s**. Sampled free VRAM reached 29 MiB.

На двух изображениях CPU Vision, 16 потоков, A/B/B/A: медианы повторов нового кодировщика примерно **3.27 с против 8.06 с** и **2.91 с против 7.27 с**. Выходы не побитово идентичны: cosine около 0.99985; реальные OCR-проверки `4217` и `STRATA 42` прошли. Это не гарантия качества на всех изображениях.

On two images, 16-thread CPU Vision A/B/B/A median encoding times were about **3.27 s vs 8.06 s** and **2.91 s vs 7.27 s**. Embeddings were not bit-identical (cosine about 0.99985); real OCR checks returned `4217` and `STRATA 42`. This does not establish quality for every image.

PR #6124 и дополнительный общий AVX не показали устойчивого ускорения всей модели. PR #6124 and additional AVX flags showed no stable whole-model gain.

## Исходники / Source

Проект основан на [Niko1221/Strata](https://github.com/Niko1221/Strata), распространяется по условиям лицензий проекта и включённых компонентов. Для сборки нужны Windows SDK, MSVC, CUDA и Rust; модель и её Q2 MTP pack предоставляются пользователем отдельно.

Based on [Niko1221/Strata](https://github.com/Niko1221/Strata), subject to the project and bundled-component licenses. Building requires Windows SDK, MSVC, CUDA and Rust; the model and Q2 MTP pack are supplied separately.

[Патчи / Patches](legacy-p40/patches/) · [Сборка установщика Desktop / Desktop installer build](legacy-p40/desktop/installer/) · [Сборка движка P40 / P40 engine build](legacy-p40/build.ps1)

Для сборки 0.1.63 укажите `-SourceDir` с проверенным checkout upstream `3142b66b` и используйте Developer PowerShell с CUDA 12.9. To rebuild 0.1.63, pass the upstream `3142b66b` checkout as `-SourceDir` and use Developer PowerShell with CUDA 12.9.

[All projects / Все проекты](https://github.com/aktalascloud)
