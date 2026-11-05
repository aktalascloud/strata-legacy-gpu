// Prototype only: lock owned ordinary Windows RAM ranges without CUDA registration.
#pragma once
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <psapi.h>
#include <algorithm>
#include <cstdint>
#include <limits>
#include <string>
#include <vector>
struct CpuRamRange { void* data; size_t bytes; };
class LockedCpuRanges {
public:
 LockedCpuRanges()=default;
 LockedCpuRanges(const LockedCpuRanges&)=delete;
 LockedCpuRanges&operator=(const LockedCpuRanges&)=delete;
 ~LockedCpuRanges(){clear();}
 uint64_t locked_pages()const{return locked_pages_;}
 uint64_t locked_bytes()const{return locked_bytes_;}
 void clear(){
  for(const auto&r:locked_)VirtualUnlock(r.data,r.bytes);
  locked_.clear();locked_pages_=locked_bytes_=0;
  if(quota_){SIZE_T lo=0,hi=0;DWORD flags=0;if(GetProcessWorkingSetSizeEx(GetCurrentProcess(),&lo,&hi,&flags)&&lo==owned_min_&&hi==owned_max_&&flags==old_flags_)SetProcessWorkingSetSizeEx(GetCurrentProcess(),old_min_,old_max_,old_flags_);}
  quota_=false;
 }
 bool lock(const std::vector<CpuRamRange>&input,std::string&error){
  if(quota_||!locked_.empty()||input.empty()){error="missing or repeated owned RAM ranges";return false;}
  SYSTEM_INFO sys{};GetSystemInfo(&sys);const size_t page=sys.dwPageSize;
  std::vector<CpuRamRange>ranges;size_t total=0;
  for(const auto&r:input){
   uintptr_t p=(uintptr_t)r.data;
   if(!p||!r.bytes||p%page||r.bytes>(std::numeric_limits<uintptr_t>::max)()-p||r.bytes>(std::numeric_limits<size_t>::max)()-(page-1)){error="invalid owned RAM extent/alignment";return false;}
   size_t rounded=(r.bytes+page-1)/page*page;
   if(rounded>(std::numeric_limits<uintptr_t>::max)()-p||rounded>(std::numeric_limits<size_t>::max)()-total){error="owned RAM extent overflow";return false;}
   // Only ordinary committed private allocations. No mapping, large-page privilege or foreign memory.
   for(size_t at=0;at<rounded;){MEMORY_BASIC_INFORMATION m{};if(!VirtualQuery((void*)(p+at),&m,sizeof m)||m.State!=MEM_COMMIT||m.Type!=MEM_PRIVATE||(m.Protect&(PAGE_NOACCESS|PAGE_GUARD))){error="owned RAM range is not committed private memory";return false;}size_t span=(uintptr_t)m.BaseAddress+m.RegionSize-(p+at);if(!span){error="invalid committed RAM region";return false;}at+=std::min(span,rounded-at);}
   ranges.push_back({r.data,rounded});total+=rounded;
  }
  std::sort(ranges.begin(),ranges.end(),[](const auto&a,const auto&b){return(uintptr_t)a.data<(uintptr_t)b.data;});
  for(size_t i=1;i<ranges.size();++i)if((uintptr_t)ranges[i-1].data+ranges[i-1].bytes>(uintptr_t)ranges[i].data){error="overlapping owned RAM ranges";return false;}
  if(!GetProcessWorkingSetSizeEx(GetCurrentProcess(),&old_min_,&old_max_,&old_flags_)||old_min_>(std::numeric_limits<SIZE_T>::max)()-(1u<<20)||total>(std::numeric_limits<SIZE_T>::max)()-old_min_-(1u<<20)){error="owned RAM quota extent overflow";return false;}
  owned_min_=old_min_+total+(1u<<20);owned_max_=std::max(old_max_,owned_min_);
  if(!SetProcessWorkingSetSizeEx(GetCurrentProcess(),owned_min_,owned_max_,old_flags_)){error="own working-set quota cannot hold locked ranges";return false;}
  quota_=true;
  for(const auto&r:ranges){if(!VirtualLock(r.data,r.bytes)){error="locking complete CPU RAM failed";clear();return false;}locked_.push_back(r);}
  std::vector<PSAPI_WORKING_SET_EX_INFORMATION>pages(65536);
  for(const auto&r:ranges)for(size_t at=0;at<r.bytes;){size_t count=std::min(pages.size(),(r.bytes-at)/page);for(size_t j=0;j<count;++j){pages[j]={};pages[j].VirtualAddress=(uint8_t*)r.data+at+j*page;}
   if(!K32QueryWorkingSetEx(GetCurrentProcess(),pages.data(),(DWORD)(count*sizeof pages[0]))){error="querying own locked RAM pages failed";clear();return false;}
   for(size_t j=0;j<count;++j){if(!pages[j].VirtualAttributes.Valid||!pages[j].VirtualAttributes.Locked||pages[j].VirtualAttributes.LargePage){error="CPU RAM page is not verified ordinary resident+locked";clear();return false;}++locked_pages_;}
   at+=count*page;
  }
  locked_bytes_=total;return true;
 }
private:
 std::vector<CpuRamRange>locked_;uint64_t locked_pages_=0,locked_bytes_=0;
 bool quota_=false;SIZE_T old_min_=0,old_max_=0,owned_min_=0,owned_max_=0;DWORD old_flags_=0;
};
