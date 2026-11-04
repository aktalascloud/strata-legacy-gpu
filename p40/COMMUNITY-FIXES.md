# Отличия от официальной Strata

Квалифицированный Windows-релиз для AVX1/Ivy Bridge и Pascal/P40; точные исходники и SHA указаны в manifests.

| Что применено | Для чего |
| --- | --- |
| O3, AVX1, CUDA 12.9/sm61, строгая FP; Pascal J96/unroll и ограничение MMQ ID | Совместимость со старым CPU/P40 и проверенные специализированные пути без AVX2/Tensor Cores. |
| Независимое извлечение байтов регистров; перенос повторных Q2 activation scales | Убрать лишнюю работу, сохранив порядок FP-вычислений и численную квалификацию. |
| Windows inherited log handles: issue #5175 | Engine/CPU vision stderr/stdout append atomically through FILE_APPEND_DATA handles; prevents overwriting earlier log lines. No generation speed claim. |
| PR #5040: потоковые tool-аргументы с буквальными закрывающими тегами | Не обрывать содержимое файлов внутри tool-call; 1553 ранее проверенных расписания разбивки потока. Уже входит в C5. |
| Проверка прав инструментов по текущему запросу; API ID отдельно от названия | Исключить устаревший каталог tools и ошибки идентификации модели/управления owner. |
| Structured output вместе с tools, обработка disconnect/ошибок и Retry-After | Корректнее выдавать ответы и ошибки API; это не ускорение генерации. |
| CPU-only vision с закреплением всех весов mmproj в RAM | Не занимать VRAM проектором и не перечитывать его веса при генерации; при нехватке RAM — отказ. |
| Без принудительной CPU affinity; проверенное graceful-переключение | Сохранять параллельную работу ПК и запускать только одну модель без kill. |

## Настройки моделей: кратко

- **Swift IQ3_S:** Q2 MTP + suffix, confidence 0.5, 14 workers, PCIe fraction 1, reserve 150 MiB; context 262144, KV q4_0/host 20480, CPU vision, xhigh. Авторские thinking T=1/top_p=0.95; instruct T=0.7/top_p=0.8. Лучший проверенный профиль, не абсолютный максимум для любых запросов.
- **DavidAU:** собственные авторские режимы и sampler; Q2 MTP и CPU vision. Auto/Adaptive/Ultra разрешены только проверенной совместимой модели.
- **DeepSeek 1017 IQ2_XXS (локальный C10/Draft PR1):** T=1/top_p=1/high75; context16384, CPU14, reserve512 MiB, Q2 DSpark/confidence0.5, CPUvision8/1024. Полный Engram103 GiB и все CPU-эксперты закреплены в RAM; GPU1694 эксперта/16.04 GB, CPU14050/120.8 GB; embeddings/mmproj также резидентны. Дополнительный Engram-кэш отключён. В коротких request effort=none сериях: confidence0.5 дал медиану11.98 ток/с при128 токенах;0.3/0.7/0.9 устойчивого выигрыша не дали. Это bounded/shared-PC замер, не глобальный максимум или patch-versus-stock. Локальный schema3 controller проверен; portable C10 ещё не выпущен, DeepSeek binary отсутствует в C8 ZIP.
- **MiniMax:** локально исключена после измеренной медианы 5.7 ток/с при требовании не ниже 10; экспериментальная совместимость исходников не означает квалифицированный runtime.

Изолированные CPU/operator ускорения не равны ускорению всей модели. Экспериментальный DeepSeek/C7 и чужие результаты на других GPU не выдаются за проверенный P40-релиз. Существующие пользовательские настройки сохраняются.
