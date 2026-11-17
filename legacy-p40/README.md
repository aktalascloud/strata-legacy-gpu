# Strata Legacy GPU

Windows x64. This build targets NVIDIA Pascal (Tesla P40, `sm_61`) and CPUs with AVX, including Ivy Bridge. Install a CUDA 12.9-compatible NVIDIA driver and the [Microsoft Visual C++ v14 x64 runtime](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist). The installer contains the engine, Python and CUDA libraries. Supply the two Swift 1.5 IQ3_S GGUF shards separately.

```bat
CONFIGURE.cmd "D:\Models\Swift-IQ3_S"
START.cmd
```

`CONFIGURE.cmd` uses a prefill chunk of 1,536 tokens, reserves 210 MiB of VRAM, and uses 16 CPU threads for Vision when the projector is present. It enables launch at Windows sign-in after configuring the model. Use `powershell -ExecutionPolicy Bypass -File tools\autostart.ps1 -Disable` to remove the sign-in entry.

If you have a prepared Q2 MTP pack, append `--mtp-dir "D:\Models\Swift-MTP\rt"` to `CONFIGURE.cmd`. The projector is loaded on the CPU when `mmproj-Qwen3.8-Flash-Next-BF16.gguf` is present. The API listens at `http://127.0.0.1:8093/v1`. `STOP.cmd` requests graceful shutdown.

To build the engine from this checkout, run `legacy-p40/build.ps1` from an x64 Visual Studio Developer PowerShell with CMake, Ninja and CUDA 12.9. The engine is written to `build-p40/strata.exe`.

The P40 build defaults to MMQ following the [Swift A/B test](#mmq-on-strata-01601). Keep the generated `strata_kq.dll` next to the engine. Pass `-Mmq OFF` to build without MMQ.

## Установка

Сборка для Windows x64, Tesla P40 (`sm_61`) и процессоров с AVX, включая Ivy Bridge. Нужны драйвер NVIDIA с поддержкой CUDA 12.9 и [Microsoft Visual C++ v14 x64](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist). Установщик содержит движок, Python и библиотеки CUDA. Два шарда GGUF модели Swift 1.5 IQ3_S укажите отдельно.

`CONFIGURE.cmd` задаёт чанк prefill 1536 токенов, резерв VRAM 210 МиБ и 16 потоков CPU Vision при наличии проектора. После настройки модели включается запуск при входе в Windows. Ключ `-Disable` у скрипта `tools\autostart.ps1` отключает этот запуск.

Параметр `--mtp-dir` принимает папку готового Q2 MTP. Если рядом с шардами есть `mmproj-Qwen3.8-Flash-Next-BF16.gguf`, Strata использует CPU для изображений. `STOP.cmd` штатно завершает работу.

Для сборки движка из репозитория запустите `legacy-p40/build.ps1` в x64 Visual Studio Developer PowerShell с CMake, Ninja и CUDA 12.9. Результат — `build-p40/strata.exe`.

Сборка для P40 включает MMQ по результатам [сравнения на Swift](#mmq-on-strata-01601). Поместите `strata_kq.dll` рядом с движком. Параметр `-Mmq OFF` отключает MMQ при сборке.

# Swift IQ3_S on Tesla P40

Hardware was a 24 GiB Tesla P40 (`sm_61`), PCIe 3.0 ×16, two Xeon E5-2697 v2 processors with 16 cores visible to Windows, and 256 GiB RAM. The build uses MSVC, the AVX ISA floor and CUDA 12.9. The source base is [Strata `dbb2d168`](https://github.com/Niko1221/Strata/commit/dbb2d168cffa8cf793d9325358809d5263c7c6b0).

Each row is the median of three OpenAI-compatible requests with 9,289 prompt tokens and 768 generated tokens. Each prompt starts with a different variant marker. The model uses Q2 MTP, context 262,144, q4_0 streaming KV and an exact expert route. The previous deployment ran alongside build preparation, so the upstream row is the primary comparison.

| Build / Сборка | Prefill, tok/s | Decode, tok/s | Total / Полное время, s |
| --- | ---: | ---: | ---: |
| Previous deployment / Прежний движок | 227.2 | 22.6 | 74.93 |
| Upstream AVX1 / sm_61 | 264.4 | 28.1 | 63.58 |
| Final 210 MiB profile / Итоговый профиль | 335.9 | 30.7 | 52.74 |

The final profile uses a 210 MiB VRAM reserve, 1,024-token prefill chunks and `STRATA_ADAPT_FETCH=2`. It preloaded 9,216 experts. The 24,366-token prompt took 99.03 s at 31.5 decode tok/s. The follow-up reused 16,384 prefix tokens and took 50.37 s at 31.6 decode tok/s. These are workload measurements. The configured context is 262,144 tokens.

## Русский

На Tesla P40 и двух Xeon E5-2697 v2 итоговый профиль обработал запрос на 9 289 входных и 768 выходных токенов за 52,74 с в медиане. Это на 17,0% меньше времени, чем у чистого upstream на этом стенде. Prefill вырос на 27,0%, генерация — на 9,3%. Чанк prefill — 1 024 токена, резерв VRAM — 210 МиБ, кэширование экспертов выполняется при PCIe-переносе.

Для промпта в 24 366 токенов получено 99,03 с и 31,5 ток/с генерации. Повторный запрос переиспользовал 16 384 токена и занял 50,37 с. Результаты относятся к указанным запросам и оборудованию.

[Patch decisions / Решения по патчам](research/patch-review.tsv) · [Profile experiments / Профили](research/profile-review.tsv) · [Upstream review / Разбор upstream](research/upstream-review.tsv)

[Follow-up tuning on both CPUs and the P40 / Донастройка двух CPU и P40](#swift-tuning-on-both-xeons-and-tesla-p40)

## MMQ on Strata 0.1.60.1

Both builds use `6399b835`, the same Swift profile, and the hardware above. Four matched prompts ran in fresh instances in OFF–ON–ON–OFF order, two requests per instance. Each request processed 9,292 input tokens, generated 768 tokens, and reused zero prompt tokens.

| MMQ | Median prefill, tok/s | Median decode, tok/s | Median total, s |
| --- | ---: | ---: | ---: |
| OFF | 323.1 | 29.85 | 54.30 |
| ON | 338.3 | 30.50 | 52.60 |

ON was faster in three of four pairs and cut median request time by 3.1%. The engine selected MMQ for all 48 expert layers in ON. In OFF the grouped expert counters recorded Strata's native int8 path. Both responses and MTP acceptance varied between builds, so the measured decode gain applies to these requests. [Individual runs and dispatch evidence](research/swift-mmq-20261116.json)

На Swift с MMQ медиана полного запроса снизилась на 3,1%. Замеры включают четыре пары запросов без переиспользования промпта. В трёх из четырёх пар MMQ выиграл по полному времени. Поэтому скрипт сборки для P40 выбирает MMQ по умолчанию.

# Swift tuning on both Xeons and Tesla P40

The current Swift profile uses MMQ, prefill 1536, a 210 MiB reserve and 14 workers. The 17 November follow-up tested MTP thresholds, draft attention, shared-expert scheduling, Pascal Q8 and prefill 2048. None established a repeatable balanced gain, so the current settings remain. [22 measured requests](research/generation-20261117.json).

## 11 November 2026

The Windows host exposes eight cores on each Xeon E5-2697 v2. The 14-worker profile places workers on logical processors 1–14, with the host thread on 0. System-wide CPU load in the two prefill controls was about 60% on NUMA node 0 and 55% on node 1. The benchmark records each node's prefill and decode utilization with `--socket-load`.

Each row below is the median of two 9,289-input, 768-output Swift IQ3_S requests. The arms used Q2 MTP, a 1,024-token prefill chunk and a 210 MiB VRAM reserve. Compare each candidate with its matching control.

| Arm | Prefill, tok/s | Decode, tok/s | End to end, s |
| --- | ---: | ---: | ---: |
| Native control, 14 workers | 326.9 | 31.0 | 53.27 |
| Tiled PCIe copy | 321.9 | 30.6 | 54.01 |
| AVX1 sign table | 327.8 | 31.4 | 52.88 |
| 12 CPU workers | 323.7 | 30.7 | 53.78 |
| 15 CPU workers | 318.2 | 30.3 | 54.62 |
| AVX1 for one-token IQ experts | 296.0 | 31.1 | 56.22 |
| Rebuilt control, 14 workers | 326.9 | 30.9 | 53.35 |
| AVX1 normal FP16 scale conversion | 333.5 | 31.1 | 52.61 |
| Dense `cublasSgemm` | 366.6 | 32.3 | 49.15 |
| Lower PCIe admission thresholds | 331.6 | 31.5 | 52.45 |

The selected AVX1 change removes work from the normal FP16 scale conversion. IQ3_S/IQ4_NL at four tokens took 2.895 ms per expert vs 3.220 ms on the CPU control. Eight row-format parity pairs passed. This operator measurement has a different scope from the API timing. The dense FP32 path passed bitwise comparison on the runtime cuBLAS in all 2,051 cases through the profile's prefill limit of 1,024. Run `gemm_f32_parity --full --max-t 1024` to repeat that check.

The existing upstream `--prompt-cache-tail` is enabled in the Swift profile. In the 24,366-token branch workload the repeat reused 23,552 tokens instead of 16,384. End-to-end time fell from 53.00 s to 28.94 s. The retained CPU pool has 14 workers, and PCIe admission retains its original thresholds.

The deployed build includes [upstream `6c642df7`](https://github.com/Niko1221/Strata/commit/6c642df7530a5a4ba2f6ae52deaa5be436271195). It passed 14 Windows process tests and the eight AVX1 row-format pairs. The deployed pair had a 49.98 s median for the standard request and 31.2 tok/s decode. The 24,366-token first request took 90.09 s, and its branch reused 23,552 tokens and took 29.08 s.

## Кратко по-русски

На обоих Xeon оставили 14 воркеров. Упрощённое AVX1-преобразование FP16 ускорило изолированную операцию IQ3_S/IQ4_NL на 10,1%. На Tesla P40 включён побитово проверенный `cublasSgemm` для плотного prefill. Резерв VRAM — 210 МиБ. При ветвлении длинного промпта дополнительный checkpoint сократил повторный запрос с 53,00 до 28,94 с.

На запущенной сборке после слияния upstream стандартный запрос занял 49,98 с в медиане, повторный запрос на 24 366 токенов — 29,08 с.
