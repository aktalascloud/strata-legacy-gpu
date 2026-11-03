// Full CPU-only Engram storage. No CUDA registration or model-file fallback after loading.
#pragma once
#include "ds4_os.hpp"
#include <algorithm>
#include <cstring>
#include <functional>
#include <limits>
#include <string>
#include <vector>

namespace strata::ds4 {
class LockedCpuRam {
public:
    LockedCpuRam() = default;
    LockedCpuRam(const LockedCpuRam&) = delete;
    LockedCpuRam& operator=(const LockedCpuRam&) = delete;
    ~LockedCpuRam() { clear(); }
    uint8_t* data() const { return data_; }
    void clear() {
#if defined(_WIN32)
        if (data_) {
            if (!large_) VirtualUnlock(data_, bytes_);
            VirtualFree(data_, 0, MEM_RELEASE);
        }
        if (quota_) {
            SIZE_T lo = 0, hi = 0; DWORD flags = 0;
            if (GetProcessWorkingSetSizeEx(GetCurrentProcess(), &lo, &hi, &flags) &&
                    lo == owned_min_ && hi == owned_max_ && flags == old_flags_)
                SetProcessWorkingSetSizeEx(GetCurrentProcess(), old_min_, old_max_, old_flags_);
        }
        quota_ = false;
#else
        if (data_) { ::munlock(data_, bytes_); os::anon_free(data_, bytes_); }
#endif
        data_ = nullptr; bytes_ = 0;
    }
    bool allocate(size_t bytes, std::string& error) {
        if (data_ || bytes == 0) { error = "invalid/repeated Engram RAM allocation"; return false; }
        bytes_ = bytes;
#if defined(_WIN32)
        const SIZE_T page = GetLargePageMinimum();
        if (page && bytes <= (std::numeric_limits<size_t>::max)() - (page - 1)) {
            const SIZE_T rounded = (bytes + page - 1) / page * page;
            data_ = static_cast<uint8_t*>(VirtualAlloc(nullptr, rounded,
                MEM_RESERVE | MEM_COMMIT | MEM_LARGE_PAGES, PAGE_READWRITE));
            if (data_) { large_ = true; return true; }
        }
        large_ = false;
        data_ = static_cast<uint8_t*>(VirtualAlloc(nullptr, bytes, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE));
        if (!data_) { error = "allocating complete Engram RAM failed"; return false; }
        if (VirtualLock(data_, bytes)) return true;
        // Only this process's working-set quota. No privileges, ACL, OS policy or CUDA mapping changes.
        if (!GetProcessWorkingSetSizeEx(GetCurrentProcess(), &old_min_, &old_max_, &old_flags_) ||
                old_min_ > (std::numeric_limits<SIZE_T>::max)() - (1u << 20) ||
                bytes > (std::numeric_limits<SIZE_T>::max)() - old_min_ - (1u << 20)) {
            error = "Engram working-set quota cannot hold the complete table"; clear(); return false;
        }
        owned_min_ = old_min_ + bytes + (1u << 20);
        owned_max_ = std::max(old_max_, owned_min_);
        if (!SetProcessWorkingSetSizeEx(GetCurrentProcess(), owned_min_, owned_max_, old_flags_)) {
            error = "raising this process's Engram lock quota failed"; clear(); return false;
        }
        quota_ = true;
        if (!VirtualLock(data_, bytes)) {
            error = "locking complete Engram RAM failed; file fallback prohibited"; clear(); return false;
        }
        return true;
#else
        data_ = static_cast<uint8_t*>(os::anon_alloc(bytes, -1, 1));
        if (!data_ || ::mlock(data_, bytes) != 0) {
            error = "locking complete Engram RAM failed; file fallback prohibited"; clear(); return false;
        }
        return true;
#endif
    }
private:
    uint8_t* data_ = nullptr;
    size_t bytes_ = 0;
#if defined(_WIN32)
    bool large_ = false, quota_ = false;
    SIZE_T old_min_ = 0, old_max_ = 0, owned_min_ = 0, owned_max_ = 0;
    DWORD old_flags_ = 0;
#endif
};

struct EgRamSpan { int file; uint64_t off, bytes; };
class EgResidentRam {
public:
    using Read = std::function<bool(int, uint64_t, size_t, void*)>;
    void clear() { spans_.clear(); bytes_ = 0; memory_.clear(); }
    uint64_t bytes() const { return bytes_; }
    bool load(std::vector<EgRamSpan> spans, uint64_t available, uint64_t keep, const Read& read, std::string& error) {
        if (bytes_ || spans.empty()) { error = "missing/repeated Engram RAM ranges"; return false; }
        std::sort(spans.begin(), spans.end(), [](const auto& a, const auto& b) {
            return a.file != b.file ? a.file < b.file : a.off < b.off;
        });
        uint64_t total = 0;
        for (size_t i = 0; i < spans.size(); ++i) {
            const auto& s = spans[i];
            if (s.file < 0 || !s.bytes || s.off > UINT64_MAX - s.bytes || total > SIZE_MAX - s.bytes ||
                    (i && spans[i-1].file == s.file && spans[i-1].off + spans[i-1].bytes > s.off)) {
                error = "invalid/overlapping Engram RAM ranges"; return false;
            }
            total += s.bytes;
        }
        if (available == ~uint64_t{0} || available <= keep || total > available - keep) {
            error = "complete Engram tables exceed available physical RAM plus required headroom"; return false;
        }
        if (!memory_.allocate(static_cast<size_t>(total), error)) return false;
        size_t at = 0;
        for (const auto& s : spans) {
            spans_.push_back({s.file, s.off, s.bytes, at});
            for (uint64_t done = 0; done < s.bytes;) {
                const size_t n = static_cast<size_t>(std::min<uint64_t>(s.bytes-done, 8u << 20));
                if (!read(s.file, s.off+done, n, memory_.data()+at+static_cast<size_t>(done))) {
                    error = "initial complete Engram table read failed"; clear(); return false;
                }
                done += n;
            }
            at += static_cast<size_t>(s.bytes);
        }
        bytes_ = total;
        return true;
    }
    const uint8_t* view(int file, uint64_t off, size_t n) const {
        for (const auto& s : spans_)
            if (s.file == file && off >= s.off && off-s.off <= s.bytes && n <= s.bytes-(off-s.off))
                return memory_.data()+s.at+static_cast<size_t>(off-s.off);
        return nullptr;
    }
private:
    struct Span { int file; uint64_t off, bytes; size_t at; };
    LockedCpuRam memory_;
    std::vector<Span> spans_;
    uint64_t bytes_ = 0;
};
} // namespace strata::ds4
