// Read three existing router tensors in memory only; compare original F32 and compact BF16 storage.
#include "../src/dsv41/ds4_kernels.cuh"
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <random>
#include <vector>
#define CHECK(x) do{if(!(x)){std::fprintf(stderr,"check line%d: %s\n",__LINE__,#x);std::exit(1);}}while(0)
#define CK(x) do{cudaError_t e=(x);if(e!=cudaSuccess){std::fprintf(stderr,"CUDA line%d: %s\n",__LINE__,cudaGetErrorString(e));std::exit(2);}}while(0)
template<class T>T* alloc(size_t n){T*p=nullptr;CK(cudaMalloc((void**)&p,n*sizeof(T)));return p;}
constexpr int D=5120,N=384,LD=1024;
constexpr float guard=76543.125f;
int main(int argc,char**argv){
 CHECK(argc==7);int count=0;CK(cudaGetDeviceCount(&count));CHECK(count==1);CK(cudaSetDevice(0));cudaStream_t s;CK(cudaStreamCreate(&s));
 auto w16=alloc<uint16_t>(N*D);auto w32=alloc<float>(N*D);auto input=alloc<float>(16*D);auto ya=alloc<float>(16*LD+32);auto yb=alloc<float>(16*LD+32);
 std::mt19937 rng(1604382);std::uniform_real_distribution<float>u(-1.f,1.f);int cases=0;size_t compared=0;
 for(int matrix=0;matrix<3;++matrix){
  std::ifstream file(argv[1+matrix*2],std::ios::binary);CHECK(bool(file));auto off=std::strtoull(argv[2+matrix*2],nullptr,10);file.seekg((std::streamoff)off);std::vector<uint16_t>raw(N*D);file.read((char*)raw.data(),raw.size()*2);CHECK(file.gcount()==(std::streamsize)(raw.size()*2));std::vector<float>expanded(raw.size());
  for(size_t i=0;i<raw.size();++i){uint32_t bits=(uint32_t)raw[i]<<16;std::memcpy(&expanded[i],&bits,4);CHECK(std::isfinite(expanded[i]));}
  CK(cudaMemcpy(w16,raw.data(),raw.size()*2,cudaMemcpyHostToDevice));CK(cudaMemcpy(w32,expanded.data(),expanded.size()*4,cudaMemcpyHostToDevice));
  for(int T:{1,5,16}){
   auto run=[&](bool compact){if(compact)strata::ds4::gemv_bf16_f32(w16,input,N,D,T,yb,LD,s);else strata::ds4::gemv_f32(w32,input,N,D,T,ya,LD,s);};
   for(int pattern=0;pattern<3;++pattern){
    std::vector<float>x(T*D),blank(T*LD+32,guard),a(blank.size()),b(blank.size());for(auto&v:x)v=pattern==0?u(rng):pattern==1?u(rng)*.0001f:0.f;if(pattern==2)for(int t=0;t<T;++t)x[t*D+(t*97)%D]=1.f;
    CK(cudaMemcpy(input,x.data(),x.size()*4,cudaMemcpyHostToDevice));CK(cudaMemcpy(ya,blank.data(),blank.size()*4,cudaMemcpyHostToDevice));CK(cudaMemcpy(yb,blank.data(),blank.size()*4,cudaMemcpyHostToDevice));run(false);run(true);CK(cudaStreamSynchronize(s));CK(cudaMemcpy(a.data(),ya,a.size()*4,cudaMemcpyDeviceToHost));CK(cudaMemcpy(b.data(),yb,b.size()*4,cudaMemcpyDeviceToHost));CHECK(std::memcmp(a.data(),b.data(),a.size()*4)==0);
    for(int t=0;t<T;++t){for(int n=0;n<N;++n)CHECK(std::isfinite(a[t*LD+n]));for(int n=N;n<LD;++n)CHECK(a[t*LD+n]==guard&&b[t*LD+n]==guard);}for(size_t n=a.size()-32;n<a.size();++n)CHECK(a[n]==guard&&b[n]==guard);
    ++cases;compared+=(size_t)T*N;std::printf("PARITY matrix=%d T=%d pattern=%d N=384 D=5120 bitexact=1 canaries=1\n",matrix,T,pattern);
   }
   if(matrix==0&&(T==1||T==5)){
    cudaEvent_t begin,end;CK(cudaEventCreate(&begin));CK(cudaEventCreate(&end));for(int arm=0;arm<4;++arm){bool compact=arm==1||arm==2;for(int i=0;i<20;++i)run(compact);CK(cudaEventRecord(begin,s));for(int i=0;i<300;++i)run(compact);CK(cudaEventRecord(end,s));CK(cudaEventSynchronize(end));float ms=0;CK(cudaEventElapsedTime(&ms,begin,end));std::printf("TIMING T=%d arm=%d compact=%d iterations=300 us=%.6f\n",T,arm,int(compact),ms*(1000.f/300));}CK(cudaEventDestroy(begin));CK(cudaEventDestroy(end));
   }
  }
 }
 for(void*p:{(void*)w16,(void*)w32,(void*)input,(void*)ya,(void*)yb})CK(cudaFree(p));CK(cudaStreamDestroy(s));std::printf("PASS router cases=%d actual_matrices=3 finite_outputs=%zu bitexact=1 canaries=1 worst=0\n",cases,compared);
}
