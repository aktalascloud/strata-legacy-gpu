#include "ds4_iq2_avx1_mode.hpp"
#include "strata/kernels/f16_bits.hpp"
#define GGML_COMMON_DECL_CPP
#include "ggml-common.h"
#include "ggml-cpu.h"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <random>
#include <vector>
#define CHECK(v)do{if(!(v)){std::fprintf(stderr,"FAIL line%d %s\n",__LINE__,#v);std::exit(1);}}while(0)
int main(){
 ggml_cpu_init();CHECK(ggml_cpu_has_avx()&&!ggml_cpu_has_avx2()&&!ggml_cpu_has_fma());
 const auto* traits=ggml_get_type_traits_cpu(GGML_TYPE_IQ2_XXS);CHECK(traits&&traits->vec_dot);const auto reference=traits->vec_dot;
 CHECK(strata::ds4::gguf::iq2_avx1_available());
 for(unsigned h=0;h<65536;++h) if((h&0x7c00)!=0x7c00){
  const float a=strata::kernels::f32_from_f16((uint16_t)h),b=ggml_fp16_to_fp32((ggml_fp16_t)h);
  CHECK(std::memcmp(&a,&b,4)==0);
 }
 std::puts("PASS finite_FP16_expansions=63488 bitexact=1");
 std::mt19937 rng(1017);size_t compared=0;int cases=0;
 for(int n:{256,2304,5120})for(int nt:{1,2,3,4,5,6,7,8})for(int pattern=0;pattern<4;++pattern){
  const int rows=32,nb=n/256;const size_t rb=nb*sizeof(block_iq2_xxs);
  std::vector<block_iq2_xxs>w((rows+2)*nb);for(auto&b:w){b.d=ggml_fp32_to_fp16(pattern==2?0.0f:0.003f);for(auto&v:b.qs)v=(uint16_t)rng();}
  if(pattern==3)for(size_t j=0;j<w.size();++j)w[j].d=(ggml_fp16_t)(1+(j%1023));
  std::vector<std::vector<block_q8_K>>a(nt,std::vector<block_q8_K>(nb));
  std::vector<std::vector<float>>y(nt,std::vector<float>(rows+2,123456.0f)),ref=y;std::vector<const void*>ap(nt);std::vector<float*>yp(nt);
  for(int t=0;t<nt;++t){for(auto&b:a[t]){b.d=(t%2?-0.01f:0.01f);for(int j=0;j<256;++j)b.qs[j]=pattern==1?(int8_t)(j-128):(int8_t)(rng()%256-128);}ap[t]=a[t].data();yp[t]=y[t].data();}
  for(int r=1;r<=rows;++r)for(int t=0;t<nt;++t)reference(n,&ref[t][r],0,(uint8_t*)w.data()+r*rb,0,ap[t],0,1);
  strata::ds4::gguf::iq2_avx1_rows((uint8_t*)w.data(),rb,n,ap.data(),nt,yp.data(),1,rows+1);
  for(int t=0;t<nt;++t){CHECK(y[t].front()==123456.0f&&y[t].back()==123456.0f);for(int r=1;r<=rows;++r){CHECK(std::isfinite(y[t][r])&&std::isfinite(ref[t][r]));if(std::memcmp(&y[t][r],&ref[t][r],4)){std::fprintf(stderr,"MISMATCH n%d nt%d pattern%d r%d t%d %.9g %.9g\n",n,nt,pattern,r,t,y[t][r],ref[t][r]);return 1;}++compared;}}
  ++cases;
 }
 std::printf("PASS cases=%d finite_outputs=%zu bitexact=1 canaries=1 GPU_calls=0\n",cases,compared);std::fflush(stdout);
 for(int n:{2304,5120})for(int nt:{1,2,3,4,5,6,7,8}){
  const int rows=256,nb=n/256;const size_t rb=nb*sizeof(block_iq2_xxs);
  std::vector<block_iq2_xxs>w(rows*nb);for(auto&b:w){b.d=ggml_fp32_to_fp16(0.003f);for(auto&v:b.qs)v=(uint16_t)rng();}
  std::vector<std::vector<block_q8_K>>a(nt,std::vector<block_q8_K>(nb));std::vector<std::vector<float>>y(nt,std::vector<float>(rows));std::vector<const void*>ap(nt);std::vector<float*>yp(nt);
  for(int t=0;t<nt;++t){for(auto&b:a[t]){b.d=0.01f;for(auto&v:b.qs)v=(int8_t)(rng()%255-127);}ap[t]=a[t].data();yp[t]=y[t].data();}
  for(int arm=0;arm<4;++arm){const bool simd=arm==1||arm==2;const int iterations=10;auto start=std::chrono::steady_clock::now();
   for(int j=0;j<iterations;++j){if(simd)strata::ds4::gguf::iq2_avx1_rows((uint8_t*)w.data(),rb,n,ap.data(),nt,yp.data(),0,rows);else for(int r=0;r<rows;++r)for(int t=0;t<nt;++t)reference(n,&y[t][r],0,(uint8_t*)w.data()+r*rb,0,ap[t],0,1);}
   double ms=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count()/iterations;
   std::printf("TIMING n=%d nt=%d rows=%d arm=%d simd=%d ms=%.6f\n",n,nt,rows,arm,(int)simd,ms);std::fflush(stdout);CHECK(std::isfinite(y[0][0]));
  }
 }
}
