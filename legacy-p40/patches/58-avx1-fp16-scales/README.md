# AVX1 FP16 scale conversion

The AVX1 IQ expert kernels use one range check and add the exponent offset directly for normal FP16 scales. The conversion preserves signed zero, subnormals, infinities and NaN payloads. The compiled AVX1 row checks passed all eight format pairs. The integer conversion was also checked over all 65,536 half bit patterns.

On the dual E5-2697 v2 host, the two-run median for IQ3_S/IQ4_NL at four tokens fell from 3.220 to 2.895 ms per expert. Two matched 9,289-input, 768-output Swift requests took 52.61 s median against 53.35 s on the rebuilt control. The small API difference is separate from the isolated CPU kernel speedup.
