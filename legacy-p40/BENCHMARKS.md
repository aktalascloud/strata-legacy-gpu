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

[Follow-up tuning on both CPUs and the P40 / Донастройка двух CPU и P40](TUNING.md)
