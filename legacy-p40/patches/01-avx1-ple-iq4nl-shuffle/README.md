# AVX1 PLE IQ4_NL shuffle

The RAM PLE reader expands packed IQ4_NL rows with an SSSE3 shuffle and SSE float multiplies in the AVX1 build. The split-half order and FP16 scale conversion follow the scalar path.

Two separate three-request Swift IQ3_S boots measured decode medians of 29.4 and 29.6 tok/s against the upstream control's 28.1. Full-request medians were 62.90 and 62.86 s against 63.58 s. The trace used 9,289 input and 768 output tokens. Cold and warm timing and MTP acceptance differ across boots.
