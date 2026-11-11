# Safe routing when the prior cannot rank a row

Adapted from the failure reported in [Strata PR #5655](https://github.com/Niko1221/Strata/pull/5655). If the warp cannot select ten valid experts or the normalization sum is invalid, it keeps the complete original route. Valid rows retain the existing addition and normalization.

Base `dbb2d168cffa8cf793d9325358809d5263c7c6b0`. The CUDA 12.9 test on Tesla P40 passed one valid top-10 row and four invalid rows. The live Swift profile sets `STRATA_ROUTE_PRIOR=0`.
