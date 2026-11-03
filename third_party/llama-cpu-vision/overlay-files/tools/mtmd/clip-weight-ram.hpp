#pragma once
// Lock the existing CPU weights, without another copy or process-wide memory policy.
#include <algorithm>
#include <cstdint>
#include <limits>
#include <string>
#include <vector>
#if defined(_WIN32)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <psapi.h>
#endif

class clip_weight_ram_lock {
public:
    clip_weight_ram_lock() = default;
    clip_weight_ram_lock(const clip_weight_ram_lock&) = delete;
    clip_weight_ram_lock& operator=(const clip_weight_ram_lock&) = delete;
    ~clip_weight_ram_lock() { clear(); }
    size_t bytes() const { return bytes_; }
    size_t locked_pages() const { return pages_; }
    void clear() {
#if defined(_WIN32)
        if (locked_) VirtualUnlock(base_, bytes_);
        if (quota_) {
            SIZE_T lo = 0, hi = 0; DWORD flags = 0;
            if (GetProcessWorkingSetSizeEx(GetCurrentProcess(), &lo, &hi, &flags) &&
                    lo == owned_min_ && hi == owned_max_ && flags == old_flags_)
                SetProcessWorkingSetSizeEx(GetCurrentProcess(), old_min_, old_max_, old_flags_);
        }
        locked_ = false; quota_ = false;
#endif
        base_ = nullptr; bytes_ = 0; pages_ = 0;
    }
    bool lock(void* base, size_t bytes, std::string& error) {
        if (base_ || !base || !bytes) { error = "invalid/repeated CPU weight lock"; return false; }
#if defined(_WIN32)
        base_ = base; bytes_ = bytes;
        if (!VirtualLock(base_, bytes_)) {
            // Same own-process quota pattern as the qualified DSV Engram allocator.
            if (!GetProcessWorkingSetSizeEx(GetCurrentProcess(), &old_min_, &old_max_, &old_flags_) ||
                    old_min_ > (std::numeric_limits<SIZE_T>::max)() - (1u << 20) ||
                    bytes > (std::numeric_limits<SIZE_T>::max)() - old_min_ - (1u << 20)) {
                error = "CPU weight lock quota overflow"; clear(); return false;
            }
            owned_min_ = old_min_ + bytes + (1u << 20);
            owned_max_ = std::max(old_max_, owned_min_);
            if (!SetProcessWorkingSetSizeEx(GetCurrentProcess(), owned_min_, owned_max_, old_flags_)) {
                error = "raising this process's CPU weight lock quota failed"; clear(); return false;
            }
            quota_ = true;
            if (!VirtualLock(base_, bytes_)) {
                error = "CPU weights cannot be locked; pageable fallback prohibited"; clear(); return false;
            }
        }
        locked_ = true;
        SYSTEM_INFO sys{}; GetSystemInfo(&sys);
        const uintptr_t page = sys.dwPageSize;
        if (!page) { error = "missing system page size"; clear(); return false; }
        const uintptr_t first = reinterpret_cast<uintptr_t>(base_) / page * page;
        const uintptr_t start = reinterpret_cast<uintptr_t>(base_);
        if (!page || bytes_ > UINTPTR_MAX - start || start + bytes_ > UINTPTR_MAX - (page - 1)) {
            error = "CPU weight page range overflow"; clear(); return false;
        }
        const uintptr_t end = (start + bytes_ + page - 1) / page * page;
        std::vector<PSAPI_WORKING_SET_EX_INFORMATION> query(4096);
        for (uintptr_t at = first; at < end;) {
            const size_t count = std::min<size_t>(query.size(), (end - at) / page);
            for (size_t i = 0; i < count; ++i) {
                query[i] = {};
                query[i].VirtualAddress = reinterpret_cast<void*>(at + i * page);
            }
            if (!K32QueryWorkingSetEx(GetCurrentProcess(), query.data(), (DWORD)(count * sizeof(query[0])))) {
                error = "cannot verify CPU weight locked pages"; clear(); return false;
            }
            for (size_t i = 0; i < count; ++i)
                if (!query[i].VirtualAttributes.Valid || !query[i].VirtualAttributes.Locked) {
                    error = "CPU weight page not resident and locked"; clear(); return false;
                }
            pages_ += count;
            at += count * page;
        }
        return true;
#else
        (void)base; (void)bytes;
        error = "strict CPU weight lock is supported by this helper only on Windows";
        return false;
#endif
    }
private:
    void* base_ = nullptr;
    size_t bytes_ = 0, pages_ = 0;
#if defined(_WIN32)
    bool locked_ = false, quota_ = false;
    SIZE_T old_min_ = 0, old_max_ = 0, owned_min_ = 0, owned_max_ = 0;
    DWORD old_flags_ = 0;
#endif
};
