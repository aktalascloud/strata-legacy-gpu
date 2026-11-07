# Preserve a declared extra I64 MMQ check

Used private publication recipe, extending patch49. I128 always requires the MMQ tile case. I64 accepts that one known extra case only when the candidate declares it and an actual receipt records it; all original26 cases, exact case-set equality, unique entries, successful exits, no quick runs, native/driver hashes and full F32 requirements remain enforced. Unknown extras and missing required cases are still rejected.

The current candidate actually ran27 cases, while the previous selected I64 candidate ran26. Both inventories are validated; no receipt was deleted, no native SHA was changed, and no GPU test was repeated. Seven synthetic case-set checks cover optional/undeclared/unknown/missing/I128 rules. The private helper itself is not a public engine overlay.
