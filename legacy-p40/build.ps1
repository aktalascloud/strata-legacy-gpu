param(
    [string]$CudaRoot = $env:CUDA_PATH,
    [ValidateRange(1,12)][int]$Jobs = 10
)
$ErrorActionPreference = 'Stop'
$source = Split-Path -Parent $PSScriptRoot
$build = Join-Path $source 'build-p40'
$msvc = (Get-Command cl.exe -ErrorAction Stop).Source
$nvcc = Join-Path $CudaRoot 'bin\nvcc.exe'
if (-not (Test-Path -LiteralPath $nvcc -PathType Leaf)) { throw 'Set CUDA_PATH to the CUDA 12.9 toolkit.' }
$arguments = @(
    '-S', $source, '-B', $build, '-G', 'Ninja', '-DCMAKE_BUILD_TYPE=Release',
    "-DCMAKE_C_COMPILER=$msvc", "-DCMAKE_CXX_COMPILER=$msvc",
    "-DCMAKE_CUDA_HOST_COMPILER=$msvc", "-DCMAKE_CUDA_COMPILER=$nvcc", "-DCUDAToolkit_ROOT=$CudaRoot",
    '-DCMAKE_CUDA_ARCHITECTURES=61', '-DCMAKE_CUDA_FLAGS=--allow-unsupported-compiler -Xcompiler=/arch:AVX',
    '-DSTRATA_ENABLE_CUDA=ON', '-DSTRATA_EXPERIMENTAL_SM60=ON', '-DSTRATA_ISA_FLOOR=avx',
    '-DSTRATA_BUILD_TESTS=OFF', '-DGGML_CCACHE=OFF'
)
& cmake @arguments
if ($LASTEXITCODE) { exit $LASTEXITCODE }
& cmake --build $build --target strata --parallel $Jobs
exit $LASTEXITCODE
