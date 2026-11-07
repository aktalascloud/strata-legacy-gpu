# 02. avx1-q2-bitplane-pair-4854

В существующей ветке `STRATA_Q2_BITPLANE` объединяет FP32 операции двух 128-битных половин в один AVX регистр. Целочисленные операции и порядок редукции сохранены. Конвертер fp16 берётся из текущего Swift.

Status: **source_present_optional_off**. CPU operation qualified; optional bit-plane mode is off in the measured Swift profile. No model TPS gain is inferred.

В существующей ветке `STRATA_Q2_BITPLANE` объединяет FP32 операции двух 128-битных половин в один AVX регистр. Целочисленные операции и порядок редукции сохранены. Конвертер fp16 берётся из текущего Swift.

База `9f7d977d220e-b612b01b-6c0399ee-99e1cac7-d0bddbd7`. Источник [Strata #4854](https://github.com/Niko1221/Strata/pull/4854), HEAD `7a68664acae21c1f46e999c3a0d4b213c1d7d319`.

Проверка наложения и сборка AVX1 прошли. В изолированном сравнении с текущей веткой bit-plane совпали все 60 928 результатов. На шести замеренных формах время оператора снизилось на 2,42–11,41%. Проверка объекта не нашла инструкций FMA, F16C, gather и BMI2 из списка контрольного сканирования. Сборка использовала `-mno-avx2 -mno-fma -mno-f16c -ffp-contract=off`.

Patch SHA256: `a5cbd0e73b603d6bb3627c844ce50accd964412d7ae2957a4703df44fdcdf198`. This is the original historical delta, with its own base/context.

Numbering gives stable catalogue IDs. Apply only an explicitly selected delta to its documented base; these historical patches overlap and include rejected experiments. The current published source is the integration reference. Measurements belong to their stated operation/model/source and are not additive.

Original third-party copyright and license statements in exported patches are retained. See [repository license](../../../../LICENSE) and [third-party notices](../../../../THIRD_PARTY_NOTICES.md).
