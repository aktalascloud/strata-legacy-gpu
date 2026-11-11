$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$runtime = Join-Path $root 'runtime'
$python = Join-Path $runtime 'python\python.exe'
$env:PYTHONNOUSERSITE = '1'
$env:PATH = (Join-Path $runtime 'cuda') + ';' + $env:PATH
$arguments = '-B "{0}"' -f (Join-Path $PSScriptRoot 'serve-swift.py')
$process = Start-Process -FilePath $python -ArgumentList $arguments -WindowStyle Hidden -Wait -PassThru `
    -RedirectStandardOutput (Join-Path $runtime 'server.log') -RedirectStandardError (Join-Path $runtime 'server.err.log')
exit $process.ExitCode
