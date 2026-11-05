#define NOMINMAX
#include "../src/dsv41/ds4_locked_ranges.hpp"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#define CHECK(x)do{if(!(x)){std::fprintf(stderr,"line%d: %s\n",__LINE__,#x);std::exit(1);}}while(0)
int main(){
 constexpr size_t bytes=64u<<20;auto*p=(uint8_t*)VirtualAlloc(nullptr,bytes,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);CHECK(p);for(size_t i=0;i<bytes;++i)p[i]=(uint8_t)(i*37+11);
 SIZE_T oldmin=0,oldmax=0;DWORD oldflags=0;CHECK(GetProcessWorkingSetSizeEx(GetCurrentProcess(),&oldmin,&oldmax,&oldflags));std::string error;LockedCpuRanges ranges;
 CHECK(!ranges.lock({},error));CHECK(!ranges.lock({{nullptr,4096}},error));CHECK(!ranges.lock({{p,0}},error));CHECK(!ranges.lock({{p+1,4096}},error));CHECK(!ranges.lock({{p,4096},{p,4096}},error));CHECK(!ranges.lock({{p,(std::numeric_limits<size_t>::max)()}},error));
 CHECK(ranges.lock({{p,bytes/2},{p+bytes/2,bytes/2}},error));CHECK(ranges.locked_bytes()==bytes);SYSTEM_INFO sys{};GetSystemInfo(&sys);CHECK(ranges.locked_pages()==bytes/sys.dwPageSize);
 CHECK(!ranges.lock({{p,4096}},error));for(size_t i=0;i<bytes;++i)CHECK(p[i]==(uint8_t)(i*37+11));
 const auto pages=ranges.locked_pages();ranges.clear();CHECK(ranges.locked_pages()==0&&ranges.locked_bytes()==0);SIZE_T lo=0,hi=0;DWORD flags=0;CHECK(GetProcessWorkingSetSizeEx(GetCurrentProcess(),&lo,&hi,&flags));CHECK(lo==oldmin&&hi==oldmax&&flags==oldflags);
 PSAPI_WORKING_SET_EX_INFORMATION info{};info.VirtualAddress=p;CHECK(K32QueryWorkingSetEx(GetCurrentProcess(),&info,sizeof info));std::printf("UNLOCK_STATE valid=%u locked=%u flags=%llu\n",(unsigned)info.VirtualAttributes.Valid,(unsigned)info.VirtualAttributes.Locked,(unsigned long long)info.VirtualAttributes.Flags);std::fflush(stdout);
 // Locked is meaningful only in the Valid view of the PSAPI union. Invalid after unlock is allowed.
 CHECK(!info.VirtualAttributes.Valid||!info.VirtualAttributes.Locked);CHECK(VirtualFree(p,0,MEM_RELEASE));
 std::printf("PASS owned_CPU_RAM_bytes=%zu verified_locked_pages=%llu bytes_unchanged=1 quota_restored=1 invalid_overlap_overflow_repeated_rejected=1 GPU_calls=0\n",bytes,(unsigned long long)pages);
}
