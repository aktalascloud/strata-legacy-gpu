// Compare the new production HC overlap with exact C14 source in a renamed reference namespace.
#include "../src/dsv41/ds4_kernels.cuh"
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <random>
#include <vector>
namespace strata::hc_reference {
void hc_mix_split(const float*, const float*, int, int, int, float, float*, unsigned*, const float*, const float*, int, int, float, float*, float*, float*, cudaStream_t);
void hc_pre_norm(const float*, const float*, const float*, int, int, int, float, float*, cudaStream_t);
}
#define CHECK(x) do { if (!(x)) { std::fprintf(stderr,"check line%d: %s\n",__LINE__,#x);std::exit(1); } } while(0)
#define CK(x) do {cudaError_t e=(x);if(e!=cudaSuccess){std::fprintf(stderr,"CUDA line%d: %s\n",__LINE__,cudaGetErrorString(e));std::exit(2);}}while(0)
template<class T>T* alloc(size_t n){T*p=nullptr;CK(cudaMalloc((void**)&p,n*sizeof(T)));return p;}
constexpr int D=5120,H=4,M=24;
constexpr float model_eps=1e-20f;
constexpr float guard=98765.25f;
struct Output{
 float *mix,*x,*pre,*post,*comb;int T;
 explicit Output(int t):T(t){mix=alloc<float>(T*32+32);x=alloc<float>(T*D+32);pre=alloc<float>(T*8+32);post=alloc<float>(T*8+32);comb=alloc<float>(T*64+32);}
 void reset(){for(auto p:parts()){std::vector<float>v(p.second,guard);CK(cudaMemcpy(p.first,v.data(),v.size()*4,cudaMemcpyHostToDevice));}}
 std::vector<std::pair<float*,size_t>>parts(){return{{mix,size_t(T*32+32)},{x,size_t(T*D+32)},{pre,size_t(T*8+32)},{post,size_t(T*8+32)},{comb,size_t(T*64+32)}};}
 ~Output(){for(auto p:parts())cudaFree(p.first);}
};
int main(){
 int count=0;CK(cudaGetDeviceCount(&count));CHECK(count==1);CK(cudaSetDevice(0));cudaStream_t s;CK(cudaStreamCreate(&s));
 float*state=alloc<float>(16*H*D),*fn=alloc<float>(M*H*D),*previous=alloc<float>(16*8),*norm=alloc<float>(D),*scale=alloc<float>(3),*base=alloc<float>(M);unsigned*cnt=alloc<unsigned>(16);
 std::mt19937 rng(4382);std::uniform_real_distribution<float>u(-1.f,1.f);int cases=0;double worst=0;
 for(int T:{1,5,16}){
  Output a(T),b(T);
  auto run=[&](bool overlap,bool with_norm,Output&o){
   if(overlap){strata::ds4::hc_mix(state,fn,H*D,M,T,model_eps,o.mix,s);strata::ds4::hc_pre_norm_split(state,previous,with_norm?norm:nullptr,D,H,T,model_eps,o.x,o.mix,scale,base,20,1e-6f,o.pre,o.post,o.comb,s);}
   else{strata::hc_reference::hc_mix_split(state,fn,H*D,M,T,model_eps,o.mix,cnt,scale,base,H,20,1e-6f,o.pre,o.post,o.comb,s);strata::hc_reference::hc_pre_norm(state,previous,with_norm?norm:nullptr,D,H,T,model_eps,o.x,s);}
  };
  for(int pattern=0;pattern<4;++pattern)for(bool with_norm:{false,true}){
   std::vector<float>h(T*H*D),w(M*H*D),p(T*8,guard),n(D),bs(M);float sc[3]={.8f,.7f,.6f};
   for(auto&v:h)v=pattern==0?u(rng):pattern==1?u(rng)*.001f:pattern==2?u(rng)*8.f:0.f;
   for(auto&v:w)v=u(rng)*.02f;for(auto&v:n)v=1.f+u(rng)*.2f;for(auto&v:bs)v=u(rng)*.05f;
   for(int t=0;t<T;++t)for(int j=0;j<H;++j)p[t*8+j]=.25f+u(rng)*.02f;
   CK(cudaMemcpy(state,h.data(),h.size()*4,cudaMemcpyHostToDevice));CK(cudaMemcpy(fn,w.data(),w.size()*4,cudaMemcpyHostToDevice));CK(cudaMemcpy(previous,p.data(),p.size()*4,cudaMemcpyHostToDevice));CK(cudaMemcpy(norm,n.data(),n.size()*4,cudaMemcpyHostToDevice));CK(cudaMemcpy(scale,sc,sizeof sc,cudaMemcpyHostToDevice));CK(cudaMemcpy(base,bs.data(),bs.size()*4,cudaMemcpyHostToDevice));CK(cudaMemset(cnt,0,16*sizeof(unsigned)));a.reset();b.reset();
   run(false,with_norm,a);run(true,with_norm,b);CK(cudaStreamSynchronize(s));
   auto aa=a.parts(),bb=b.parts();size_t compared=0;
   for(size_t k=0;k<aa.size();++k){std::vector<float>x(aa[k].second),y(bb[k].second);CK(cudaMemcpy(x.data(),aa[k].first,x.size()*4,cudaMemcpyDeviceToHost));CK(cudaMemcpy(y.data(),bb[k].first,y.size()*4,cudaMemcpyDeviceToHost));CHECK(std::memcmp(x.data(),y.data(),x.size()*4)==0);for(size_t j=0;j<x.size();++j){CHECK(std::isfinite(x[j]));worst=std::max(worst,double(std::fabs(x[j]-y[j])));}for(size_t j=x.size()-32;j<x.size();++j)CHECK(x[j]==guard&&y[j]==guard);compared+=x.size();}
   std::printf("PARITY T=%d H=4 D=5120 pattern=%d norm=%d floats=%zu bitexact=1 canary=1\n",T,pattern,int(with_norm),compared);++cases;
  }
  if(T==1||T==5){
   cudaEvent_t begin,end;CK(cudaEventCreate(&begin));CK(cudaEventCreate(&end));
   for(int arm=0;arm<4;++arm){bool overlap=arm==1||arm==2;for(int i=0;i<20;++i)run(overlap,true,overlap?b:a);CK(cudaEventRecord(begin,s));for(int i=0;i<500;++i)run(overlap,true,overlap?b:a);CK(cudaEventRecord(end,s));CK(cudaEventSynchronize(end));float ms=0;CK(cudaEventElapsedTime(&ms,begin,end));std::printf("TIMING T=%d arm=%d overlap=%d iterations=500 us=%.6f\n",T,arm,int(overlap),ms*2.f);}
   CK(cudaEventDestroy(begin));CK(cudaEventDestroy(end));
  }
 }
 for(void*p:{(void*)state,(void*)fn,(void*)previous,(void*)norm,(void*)scale,(void*)base,(void*)cnt})CK(cudaFree(p));CK(cudaStreamDestroy(s));std::printf("PASS HC cases=%d bitexact=1 canaries=1 worst=%.9g\n",cases,worst);
}
