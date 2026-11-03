// Measured on P40 against the existing sm_61 table, with bitwise parity. Only this exact matrix is qualified.
#pragma once
namespace strata::kernels {
struct Sm61Q6HeadChoice { int pf = 0, rows = 0; };
constexpr Sm61Q6HeadChoice sm61_q6_head_choice(int cc, int type, int n_in, int n_out, int columns) {
    if (cc != 61 || type != 14 || n_in != 2560 || n_out != 248320) return {};
    if (columns == 2) return {3, 2};  // 2480.7 -> 2168.5 us: exact integer forms, two rows a warp
    if (columns == 4) return {6, 2};  // 2716.9 -> 2465.2 us: hoisted loads, original arithmetic
    return {};                     // three columns keep the faster existing four-row kernel
}
static_assert(sm61_q6_head_choice(61,14,2560,248320,2).pf == 3);
static_assert(sm61_q6_head_choice(61,14,2560,248320,4).pf == 6);
static_assert(sm61_q6_head_choice(61,14,2560,248320,3).pf == 0);
static_assert(sm61_q6_head_choice(61,14,2560,248320,1).pf == 0);
static_assert(sm61_q6_head_choice(61,14,2560,248320,5).pf == 0);
static_assert(sm61_q6_head_choice(60,14,2560,248320,2).pf == 0);
static_assert(sm61_q6_head_choice(80,14,2560,248320,2).pf == 0);
static_assert(sm61_q6_head_choice(61,13,2560,248320,2).pf == 0);
static_assert(sm61_q6_head_choice(61,14,6144,248320,2).pf == 0);
static_assert(sm61_q6_head_choice(61,14,2560,106299,2).pf == 0);
} // namespace strata::kernels
