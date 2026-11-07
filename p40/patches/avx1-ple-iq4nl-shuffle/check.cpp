#include "strata/kernels/ngram.hpp"
#include "ggml.h"
#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <vector>

namespace strata::kernels {
void iq4nl_dequant_row_baseline(const uint8_t*, float*);
}
using Fn = void(*)(const uint8_t*,float*);
volatile float sink_value = 0.0f;
static uint32_t random_state = 138031;
static uint32_t next_random() {
    random_state ^= random_state << 13;
    random_state ^= random_state >> 17;
    random_state ^= random_state << 5;
    return random_state;
}
static void fill(uint8_t* row, uint16_t scale, unsigned pattern) {
    for (int block = 0; block < 5; ++block) {
        std::memcpy(row + block * 18, &scale, 2);
        for (int j = 0; j < 16; ++j)
            row[block * 18 + 2 + j] = pattern == 0 ? uint8_t(j | ((15-j)<<4)) : uint8_t(next_random());
    }
}
static double bench(Fn f, const std::vector<uint8_t>& rows, int row_count) {
    std::array<float,160> output{};
    const auto start = std::chrono::steady_clock::now();
    float checksum = 0.0f;
    constexpr int iterations = 200000;
    for (int i = 0; i < iterations; ++i) {
        const int index = (i * 1013u) & (row_count-1);
        f(rows.data()+size_t(index)*90,output.data());
        checksum += output[size_t(i)%160];
    }
    sink_value = checksum;
    return std::chrono::duration<double,std::nano>(std::chrono::steady_clock::now()-start).count()/iterations;
}
int main() {
    ggml_context* context=ggml_init({1u<<20,nullptr,true});
    if (!context) return 2;
    const auto* traits=ggml_get_type_traits(GGML_TYPE_IQ4_NL);
    if (!traits || !traits->to_float) return 3;
    std::array<uint8_t,90+32> packed{};
    std::array<uint32_t,176> old_bits{},new_bits{},ref_bits{};
    uint64_t rows_checked=0,ggml_checked=0;
    for (unsigned scale=0;scale<65536;++scale) {
        for (int shift : {0,1,7,15}) {
            const unsigned pattern=unsigned(shift)&1;
            fill(packed.data()+shift,uint16_t(scale),pattern);
            old_bits.fill(0x5a3cf017u);new_bits=old_bits;ref_bits=old_bits;
            const int out_shift=4+(shift&3);
            float* a=reinterpret_cast<float*>(old_bits.data()+out_shift);
            float* b=reinterpret_cast<float*>(new_bits.data()+out_shift);
            strata::kernels::iq4nl_dequant_row_baseline(packed.data()+shift,a);
            strata::kernels::iq4nl_dequant_row(packed.data()+shift,b);
            if (old_bits!=new_bits) {
                std::printf("DIFF scale=%u shift=%d\n",scale,shift);return 1;
            }
            if ((scale & 0x7c00u)!=0x7c00u && shift==0) {
                traits->to_float(packed.data(),reinterpret_cast<float*>(ref_bits.data()+out_shift),160);
                if (new_bits!=ref_bits) {
                    std::printf("GGML DIFF scale=%u\n",scale);return 1;
                }
                ++ggml_checked;
            }
            ++rows_checked;
        }
    }
    std::printf("PARITY rows=%llu ggml=%llu bit_differences=0 bounds=pass\n",
                (unsigned long long)rows_checked,(unsigned long long)ggml_checked);
    for (int count : {16,16384}) {
        std::vector<uint8_t> data(size_t(count)*90);
        for (int i=0;i<count;++i) fill(data.data()+size_t(i)*90,uint16_t(0x1800u+next_random()%0x3000u),1);
        for (int r=0;r<6;++r) {
            const bool new_first=(r&1)!=0;
            double old_ns,new_ns;
            if (new_first) {
                new_ns=bench(strata::kernels::iq4nl_dequant_row,data,count);
                old_ns=bench(strata::kernels::iq4nl_dequant_row_baseline,data,count);
            } else {
                old_ns=bench(strata::kernels::iq4nl_dequant_row_baseline,data,count);
                new_ns=bench(strata::kernels::iq4nl_dequant_row,data,count);
            }
            std::printf("TIME rows=%d round=%d old_ns=%.3f new_ns=%.3f\n",count,r,old_ns,new_ns);
        }
    }
    ggml_free(context);
    return 0;
}
