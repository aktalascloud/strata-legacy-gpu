#pragma once
// CPU-preencoded DeepSeek-4.1 blocks. DSE1 does not carry RGB or a GPU encoder request.
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <memory>
#include <string>
#include <vector>

namespace strata::ds4 {
struct ExternalImage {
    int64_t start = 0;
    uint64_t hash = 0;
    std::shared_ptr<const std::vector<uint16_t>> rows;
};

// Called after DSE1 magic: int32 count; each record int64 start, int32 rows, int32 dim, F32[rows][dim].
inline bool read_external_images(std::FILE* f, int dim, size_t budget,
                                 std::vector<ExternalImage>& out, std::string& err) {
    const auto fail = [&]() { out.clear(); err = "invalid CPU image embeddings (DSE1)"; return false; };
    int32_t count = 0;
    if (dim <= 0 || budget == 0 || std::fread(&count, 4, 1, f) != 1 || count < 0 || count > 4096) return fail();
    size_t total = 0;
    int64_t last_end = 0;
    std::vector<float> row((size_t) dim);
    for (int i = 0; i < count; ++i) {
        ExternalImage p;
        int32_t n = 0, d = 0;
        if (std::fread(&p.start, 8, 1, f) != 1 || std::fread(&n, 4, 1, f) != 1 ||
            std::fread(&d, 4, 1, f) != 1 || p.start < last_end || n <= 0 || n > 65536 || d != dim ||
            (uint64_t) p.start >= budget || (size_t) n >= budget - (size_t) p.start ||
            (size_t) n > budget - total || (size_t) n > SIZE_MAX / (size_t) dim) return fail();
        total += (size_t) n;
        last_end = p.start + n; // bounded by budget above; leaves at least one final text token
        auto rows = std::make_shared<std::vector<uint16_t>>();
        uint64_t hash = 1469598103934665603ull;
        const auto add = [&](const void* ptr, size_t len) {
            const auto* b = static_cast<const uint8_t*>(ptr);
            for (size_t k = 0; k < len; ++k) hash = (hash ^ b[k]) * 1099511628211ull;
        };
        add(&p.start, 8); add(&n, 4); add(&d, 4);
        for (int r = 0; r < n; ++r) {
            if (std::fread(row.data(), 4, (size_t) dim, f) != (size_t) dim) return fail();
            add(row.data(), (size_t) dim * 4);
            rows->resize(rows->size() + (size_t) dim);
            for (int c = 0; c < dim; ++c) {
                if (!std::isfinite(row[(size_t) c])) return fail();
                uint32_t u;
                std::memcpy(&u, &row[(size_t) c], 4);
                // Same round-to-nearest-even conversion as Model::read_bf16.
                const uint16_t b = (uint16_t) ((u + 0x7fffu + ((u >> 16) & 1u)) >> 16);
                if ((b & 0x7f80u) == 0x7f80u) return fail(); // finite F32 must not overflow to BF16 infinity
                (*rows)[(size_t) r * dim + c] = b;
            }
        }
        p.hash = hash;
        p.rows = std::move(rows);
        out.push_back(std::move(p));
    }
    if (std::fgetc(f) != EOF || std::ferror(f)) return fail();
    return true;
}
} // namespace strata::ds4
