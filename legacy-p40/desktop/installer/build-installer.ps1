param(
  [Parameter(Mandatory)][ValidatePattern('^[a-fA-F0-9]{64}$')][string]$IntegritySha256,
  [Parameter(Mandatory)][string]$Output,
  [Parameter(Mandatory)][string]$Nsis,
  [Parameter(Mandatory)][ValidateNotNullOrEmpty()][string[]]$PrivatePrefix,
  [Parameter(Mandatory)][string]$Stage,
  [ValidatePattern('^\d+\.\d+\.\d+\.\d+$')][string]$Version = '0.2.15.5',
  [switch]$Qualification
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if (-not [IO.Path]::IsPathRooted($Stage)) { throw 'Provide an absolute staging path.' }
$stage = (Resolve-Path -LiteralPath $Stage).Path
$manifest = Join-Path $stage 'bundle-integrity.json'
if (-not $Qualification -and (Test-Path -LiteralPath (Join-Path $stage 'RELEASE-BLOCKED.txt'))) { throw 'This payload is not qualified for release.' }
if (-not [IO.Path]::IsPathRooted($Nsis) -or -not (Test-Path -LiteralPath $Nsis -PathType Leaf)) { throw 'Provide an existing absolute makensis path.' }
if (@($PrivatePrefix | Where-Object { [string]::IsNullOrWhiteSpace($_) }).Count) { throw 'Private path prefixes must not be empty.' }
$scanPrefixes = @($PrivatePrefix) + @($PSScriptRoot)
if (-not [string]::IsNullOrWhiteSpace($env:USERPROFILE)) { $scanPrefixes += $env:USERPROFILE }
$out = [IO.Path]::GetFullPath($Output)
if (-not [IO.Path]::IsPathRooted($Output) -or [IO.Path]::GetExtension($out) -ine '.exe') { throw 'Provide an absolute output path ending in .exe.' }
if (Test-Path -LiteralPath $out) { throw 'Existing installer retained.' }
if ((Get-FileHash -LiteralPath $manifest -Algorithm SHA256).Hash -ine $IntegritySha256) { throw 'The reviewed payload manifest changed.' }
$launcher = Get-Content -LiteralPath (Join-Path $stage 'tools\start-desktop.ps1') -Raw
if (-not $launcher.Contains($IntegritySha256.ToLowerInvariant())) { throw 'The launcher does not pin this integrity manifest.' }
$scanArgs = @((Join-Path $PSScriptRoot 'scan_payload.py'), $stage)
foreach ($prefix in $scanPrefixes) { $scanArgs += @('--private-prefix',$prefix) }
& (Join-Path $stage 'app\control\python\python.exe') -B @scanArgs
if ($LASTEXITCODE) { throw 'Privacy/model scan failed; installer not built.' }
$defines = @("/DPAYLOAD=$stage", "/DOUTPUT=$out", "/DINTEGRITY_SHA256=$($IntegritySha256.ToLowerInvariant())", "/DVERSION=$Version")
if ($Qualification) { $defines += '/DQUALIFICATION' }
& $Nsis /INPUTCHARSET UTF8 /WX @defines (Join-Path $PSScriptRoot 'setup.nsi')
if ($LASTEXITCODE) { throw 'NSIS build failed; inspect any partial output before retrying.' }
Get-FileHash -LiteralPath $out -Algorithm SHA256
