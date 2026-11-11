#include "strata/kernels/route_prior.hpp"

#include <cuda_runtime.h>
#include <array>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <limits>

void check(cudaError_t error) {
    if (error != cudaSuccess) {
        std::fprintf(stderr, "%s\n", cudaGetErrorString(error));
        std::exit(1);
    }
}

int main() {
    constexpr int experts = 512, picks = 10, rows = 5;
    std::array<float, rows * experts> logits;
    std::array<int32_t, experts> residency;
    std::array<int32_t, rows * picks> ids;
    std::array<float, rows * picks> weights;
    const float inf = std::numeric_limits<float>::infinity();
    logits.fill(-inf);
    residency.fill(-1);
    for (int e = 0; e < experts; ++e) {
        logits[e] = e * 0.01f;
        logits[experts + e] = std::numeric_limits<float>::quiet_NaN();
        logits[4 * experts + e] = e * 0.01f;
    }
    logits[3 * experts + 7] = 1.0f;
    logits[4 * experts + 42] = inf;
    for (int i = 0; i < rows * picks; ++i) {
        ids[i] = 20 + i;
        weights[i] = 0.03125f * (1 + i);
    }
    const auto original_ids = ids;
    const auto original_weights = weights;
    float *gpu_logits, *gpu_weights;
    int32_t *gpu_residency, *gpu_ids;
    check(cudaMalloc(&gpu_logits, sizeof(logits)));
    check(cudaMalloc(&gpu_residency, sizeof(residency)));
    check(cudaMalloc(&gpu_ids, sizeof(ids)));
    check(cudaMalloc(&gpu_weights, sizeof(weights)));
    check(cudaMemcpy(gpu_logits, logits.data(), sizeof(logits), cudaMemcpyHostToDevice));
    check(cudaMemcpy(gpu_residency, residency.data(), sizeof(residency), cudaMemcpyHostToDevice));
    check(cudaMemcpy(gpu_ids, ids.data(), sizeof(ids), cudaMemcpyHostToDevice));
    check(cudaMemcpy(gpu_weights, weights.data(), sizeof(weights), cudaMemcpyHostToDevice));
    strata::kernels::route_prior_top10(gpu_logits, gpu_residency, 1.5f, gpu_ids, gpu_weights, rows, nullptr);
    check(cudaGetLastError());
    check(cudaMemcpy(ids.data(), gpu_ids, sizeof(ids), cudaMemcpyDeviceToHost));
    check(cudaMemcpy(weights.data(), gpu_weights, sizeof(weights), cudaMemcpyDeviceToHost));
    check(cudaFree(gpu_weights));
    check(cudaFree(gpu_ids));
    check(cudaFree(gpu_residency));
    check(cudaFree(gpu_logits));
    float sum = 0.0f;
    for (int i = 0; i < picks; ++i) {
        if (ids[i] != experts - 1 - i || !(weights[i] > 0.0f)) return 2;
        sum += weights[i];
    }
    if (std::abs(sum - 1.0f) > 1e-5f) return 3;
    for (int i = picks; i < rows * picks; ++i) {
        if (ids[i] != original_ids[i] || weights[i] != original_weights[i]) return 4;
    }
    std::puts("Route prior: valid top 10 and four preserved invalid routes passed.");
}
