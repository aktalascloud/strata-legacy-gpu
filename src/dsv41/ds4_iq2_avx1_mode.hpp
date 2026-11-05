#pragma once
#include <cstddef>
#include <cstdint>
namespace strata::ds4::gguf {
bool iq2_avx1_available();
bool iq2_avx1_enabled();
// Internal NT1..8 row entry, also linked directly by the CPU qualification fixture.
void iq2_avx1_rows(const uint8_t* w, size_t rb, int n, const void* const* act, int nt, float* const* out, int r0, int r1);
}
