# Exact P40 expert format table

Selected and enabled in the primary Swift profile with STRATA_SM61_EXPERT_TABLE=1. Base public revision f049d0f3925c61f1c3740e686462903b6dc403db; official source 146df3c468739147f520ac3816de806f71232571. Original weights, router choices and arithmetic kernels are retained. Only local host dispatch/auto GU row budgeting changes. Explicit EXP_MODE, old/v1, Hadamard, nibble, strided and non-SM61 paths bypass the table.

GU18/22 at2560x640/cap10..40 use existing EXPDEC with local auto minimum400; down20 keeps the CUDA layout and down42 keeps LDS mode8. Other geometries/formats keep the existing choice. First-install Swift defaults opt in; existing configurations are never reset.

Actual final native passed112 layout/T/grid pairs direct and Graph bitwise,130 Q8 shape/column checks (one expected shared-memory decline per mode) and all required package/F32 checks. Three rotating-weight direct timing rounds at T3 improved selected expert operations2.9-6.9%; direct timing includes host dispatch overhead. Graph output was checked, Graph timing was not measured. Same-native model medians 39.2/38.6tok/s, observed -1.53%; established overall TPS gain: False. This is no absolute maximum or broad model-quality benchmark.

The public LF source is exactly the qualified private source after CRLF normalization. The canonical patch includes the native delta and qualified first-install default/test. It requires its original context and is not an arbitrary-upstream concatenation series. CPUvision is reused by exact closure; context262144, reserve150MiB,14workers,Q2 MTP/spec3/.5/suffix3,PCIe1,q4_0 KV/host20480 and standard xhigh are preserved.
