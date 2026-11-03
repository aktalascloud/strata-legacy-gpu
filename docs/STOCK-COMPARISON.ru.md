# Отличия от stock Strata 1.56: C5

База — официальный commit `ffa80d73133ea5c548aefe57889a16e8085a938f`. Полный reviewed aggregate: `948ac64cdc7fc016bf389f834be79354fbf15142419b96a9661b10116eb35f56`. Этот список описывает локальную интеграцию C5 и новый подготовленный пакет; прежние ZIP r2 не меняются.

- **AVX1/Pascal:** фиксированный O3/Ivy Bridge и CUDA12.9/sm61/CA; строгая CPU/host FP, безопасные wider-ISA guards и отсутствие принудительного CPU pinning.
- **CPU/GPU:** локальные Q2/IQ row-оптимизации, Pascal MMQ overlay и узкий Q6 head dispatch; пользовательские явные overrides сохраняют приоритет. Уже имеющиеся в stock возможности не выдаются за отдельное изобретение форка.
- **Загрузка/память:** overlapped dense/expert загрузка, проверенные Windows uploads, lifetime/границы GGUF/PLE/MMQ и BF16 NaN guards. Native E4 переиспользован точно; GPU-математика C5 не пересобиралась.
- **CPU vision99E1:** все существующие buffers весов mmproj закрепляются в RAM без второй копии. Проверяются Valid+Locked страницы; нехватка квоты/памяти вызывает отказ. Изменяется только собственная working-set quota процесса, без привилегий, affinity или системной NUMA policy. Новый native preset включает require_ram; elastic/lazy reload не используется.
- **Q2 MTP:** каталог с опубликованным базовым Qwen3.8 Q2 runtime и проверенным словарём425196 байт. Это не Swift-trained draft. Lookup-chain в reference preset выключен; наличие кода lookup не объявлено включённым ускорением.
- **Serving/API:** bounded incremental parsing, authority текущих tools, корректные ID/display name, error envelopes/SSE, JSON/Responses/Anthropic проверки. Статус incomplete и socket-stall не превращаются в отмену принятых запросов.
- **Жизненный цикл:** один owner, штатный drain и QUIT/EOF, запрет замены неподтверждённого процесса. Новый source-specific schema3 review; старые GPU receipts не переименовываются в новые прогоны.

## Проверенная часть пакета

Classic native E4 сохраняет исходные27 numerical/Graph проверок и полный DenseF32 sweep5201. Его CUDA-библиотеки и исходный compiler origin сохранены; C5 aggregate948A не выдаётся за исходник новой компиляции E4. CPU vision99E1 — отдельная новая CPU-сборка: реальные Qwen907523008 байт/221564 locked pages, DeepSeek972189696/237352 pages. Один CPU encode покрывает Swift/DavidAU по доказанному равенству334 тензоров/полезной нагрузки и эффективного tokenizer. После штатного запуска classic-модель правильно ответила на синтетическое изображение с красной и синей половинами. Это функциональная проверка, не оценка произвольных изображений.

## Экспериментальные исходники

**DeepSeek4.1:** sm61 WMMA guards из PR4376, исправление multipart RAM DMA из4969, Windows/AVX1 совместимость, require-ram для полного expert complement/Engram/embedding без model-file fallback; CPU DeepSeek41v image bridge и точный DSpark/Q2 путь. Пятнадцать небольших numerical cases реально прошли; parser общего runner не распознал многословный RESULT. Оставшиеся9 команд, полный запуск модели, реальное размещение огромного Engram и её CPUimage ответ ещё не квалифицированы. DeepSeek native binary и веса в ZIP не входят. Чужие sm86/sm120 результаты не считаются P40 доказательством.

**MiniMax3.1:** исходники интеграции Project Maya, собственный tokenizer/thinking/tool формат и DSpark сохраняются с лицензиями/атрибуцией. Совместимый MiniMax Q2 draft не квалифицирован; её model assets/native runtime в этот ZIP не включены. Загрузка mmproj сама по себе не доказывает работающую vision интеграцию.

Оригинальные лицензии Strata, ggml/Pascal overlay и Project Maya сохранены. Built with MiniMax M3.1-Flash.

Текущий matched throughput gain не измерен. Исторические +15.27% относятся к явно указанной старой версии/нагрузкам и не переносятся на C5. Не заявляются абсолютный максимум на любых запросах, полное покрытие PR/issues или отсутствие всех уязвимостей.
