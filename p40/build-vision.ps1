[CmdletBinding()]
param([string]$Clang='clang-cl.exe',[string]$LlamaSource='', [ValidateRange(1,12)][int]$Jobs=12)
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$profile=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'build-profile.json') -Raw -Encoding UTF8|ConvertFrom-Json
$pins=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'patches/manifest.json') -Raw -Encoding UTF8|ConvertFrom-Json
foreach($name in @('git','tar','python','cmake','ninja','cl.exe',$Clang)){if(-not(Get-Command $name -ErrorAction SilentlyContinue)){throw "Missing prerequisite: $name"}}
if(-not $LlamaSource){$LlamaSource=Join-Path $root '.p40-deps/llama.cpp'}
if(-not(Test-Path -LiteralPath $LlamaSource)){throw 'Provide the existing pinned llama.cpp checkout from p40/build.ps1; this helper does not download any model or runtime.'}
$compiler=(Get-Command $Clang).Source;$llvm=Split-Path -Parent (Split-Path -Parent $compiler)
$omp=Join-Path $llvm 'lib/libomp.lib';if(-not(Test-Path -LiteralPath $omp)){throw 'Reference Clang23.1.4 libomp.lib is required.'}
$work=Join-Path $root ('work/vision-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+[Guid]::NewGuid().ToString('N').Substring(0,8))
[IO.Directory]::CreateDirectory($work)|Out-Null
$copy=Join-Path $work 'llama.cpp';[IO.Directory]::CreateDirectory($copy)|Out-Null
$archive=Join-Path $work 'pinned-dependency.tar'
& git -c core.autocrlf=false -C $LlamaSource archive --format=tar --output=$archive $pins.ggml_sha
if($LASTEXITCODE -ne 0){throw 'Pinned dependency archive failed; no source checkout was changed.'}
& tar -xf $archive -C $copy
if($LASTEXITCODE -ne 0){throw 'Dependency extraction failed.'}
& python -B (Join-Path $root 'tools/vision/apply_llama_overlay.py') --llama-dir $copy
if($LASTEXITCODE -ne 0){throw 'Exact353-input dependency overlay check failed.'}
$args=@('-S',(Join-Path $root 'tools/vision'),'-B',(Join-Path $work 'build'),'-G','Ninja','-DCMAKE_BUILD_TYPE=Release',"-DCMAKE_C_COMPILER=$compiler","-DCMAKE_CXX_COMPILER=$compiler",'-DCMAKE_LINKER=link.exe',('-DCMAKE_C_FLAGS_RELEASE='+$profile.cpu_release_flags),('-DCMAKE_CXX_FLAGS_RELEASE='+$profile.cpu_release_flags),'-DCMAKE_EXPORT_COMPILE_COMMANDS=ON','-DCMAKE_INTERPROCEDURAL_OPTIMIZATION=OFF',"-DLLAMA_DIR=$copy",'-DSTRATA_PORTABLE=OFF','-DGGML_NATIVE=OFF','-DSTRATA_VISION_CUDA=OFF','-DSTRATA_VISION_HIP=OFF','-DSTRATA_VISION_SYCL=OFF','-DSTRATA_VISION_METAL=OFF','-DGGML_AVX2=OFF','-DGGML_FMA=OFF','-DGGML_F16C=OFF','-DGGML_BMI2=OFF','-DGGML_AVX512=OFF','-DGGML_AVX512_VBMI=OFF','-DGGML_AVX512_VNNI=OFF','-DGGML_AVX512_BF16=OFF','-DGGML_AVX_VNNI=OFF','-DGGML_AMX_TILE=OFF','-DGGML_AMX_INT8=OFF','-DGGML_AMX_BF16=OFF','-DGGML_CPU_ALL_VARIANTS=OFF','-DGGML_CCACHE=OFF','-DGGML_LTO=OFF','-DGGML_BLAS=OFF','-DGGML_ACCELERATE=OFF','-DOpenMP_C_FLAGS=/clang:-fopenmp','-DOpenMP_CXX_FLAGS=/clang:-fopenmp','-DOpenMP_C_LIB_NAMES=libomp','-DOpenMP_CXX_LIB_NAMES=libomp',"-DOpenMP_libomp_LIBRARY=$omp",'-DGGML_VULKAN=OFF','-DGGML_OPENCL=OFF','-DGGML_WEBGPU=OFF','-DGGML_RPC=OFF','-DGGML_MUSA=OFF','-DGGML_CANN=OFF')
& cmake @args
if($LASTEXITCODE -ne 0){throw 'CPU vision configure failed.'}
$env:STRATA_NO_CPU_PIN='1';$env:CMAKE_BUILD_PARALLEL_LEVEL=[string]$Jobs
& cmake --build (Join-Path $work 'build') --target strata-vision --parallel $Jobs
if($LASTEXITCODE -ne 0){throw 'CPU vision build failed.'}
Write-Output "Built CPU-only AVX1 helper in $work. The base dependency checkout was not changed. New bytes need source/CPU lock/encode qualification before use."
