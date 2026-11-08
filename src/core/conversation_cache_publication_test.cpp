#ifndef EXPECT_ORIGINAL_BUG
#define EXPECT_ORIGINAL_BUG 0
#endif
#include "strata/core/conversation_cache.hpp"
#include <atomic>
#include <cstdio>
#include <cstdlib>
#include <new>
#include <vector>
static std::atomic<long> fail_n{0};
void* operator new(size_t n){if(fail_n.load()>0&&fail_n.fetch_sub(1)==1){fail_n=0;throw std::bad_alloc();}if(void*p=std::malloc(n?n:1))return p;throw std::bad_alloc();}
void* operator new[](size_t n){return ::operator new(n);}
void operator delete(void*p)noexcept{std::free(p);}
void operator delete[](void*p)noexcept{std::free(p);}
void operator delete(void*p,size_t)noexcept{std::free(p);}
void operator delete[](void*p,size_t)noexcept{std::free(p);}
using namespace strata::core;
static SavedConversation make_image(int key){SavedConversation s;s.live.ids={key,key+1};s.live.gdn.resize(64,7);s.cvec=true;return s;}
int main(){int failures=0,bugs=0,cases=0;
 for(int before=0;before<8;++before)for(int nth=1;nth<=8;++nth){
  ConversationCache c(1<<20,16);
  for(int i=0;i<before;++i){auto s=make_image(100+i*10);if(!c.put(std::move(s)))return 2;}
  auto image=make_image(9999);const auto ids=image.live.ids;const auto bytes=image.bytes(),old_bytes=c.bytes();bool caught=false;
  fail_n=nth;
  try{if(!c.put(std::move(image)))return 3;}catch(const std::bad_alloc&){caught=true;}
  fail_n=0;++cases;
  if(caught){
   ++failures;const bool intact=c.size()==size_t(before)&&c.bytes()==old_bytes&&image.live.ids==ids&&image.live.gdn.size()==64;
   if(!intact){++bugs;if(!EXPECT_ORIGINAL_BUG){std::printf("FAIL publication after allocation failure before=%d nth=%d\n",before,nth);return 1;}continue;}
   if(!c.put(std::move(image)))return 4;
  }
  if(!EXPECT_ORIGINAL_BUG){
   if(c.size()!=size_t(before+1)||c.bytes()!=old_bytes+bytes)return 5;
   auto q=ids;q.push_back(8);auto m=c.best(q,{},true);if(m.tokens!=2||!m.serial||!c.find(m.serial))return 6;
  }
 }
 if(!failures||bool(bugs)!=bool(EXPECT_ORIGINAL_BUG))return 7;
 std::printf("cache publication: %d cases, %d injected failures, %d broken-state observations, expected_original=%d PASS\n",cases,failures,bugs,EXPECT_ORIGINAL_BUG);return 0;
}
