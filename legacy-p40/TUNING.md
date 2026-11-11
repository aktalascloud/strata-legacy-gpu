# Swift tuning on both Xeons and Tesla P40

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
