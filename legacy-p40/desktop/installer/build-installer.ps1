param(
  [Parameter(Mandatory)][ValidatePattern('^[a-fA-F0-9]{64}$')][string]$IntegritySha256,
  [Parameter(Mandatory)][string]$Output,
  [Parameter(Mandatory)][string]$Nsis,
  [Parameter(Mandatory)][ValidateNotNullOrEmpty()][string[]]$PrivatePrefix
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$stage = Join-Path $PSScriptRoot 'payload'
$manifest = Join-Path $stage 'bundle-integrity.json'
if (-not [IO.Path]::IsPathRooted($Nsis) -or -not (Test-Path -LiteralPath $Nsis -PathType Leaf)) { throw 'Provide an existing absolute makensis path.' }
if (@($PrivatePrefix | Where-Object { [string]::IsNullOrWhiteSpace($_) }).Count) { throw 'Private path prefixes must not be empty.' }
$scanPrefixes = @($PrivatePrefix) + @($PSScriptRoot)
if (-not [string]::IsNullOrWhiteSpace($env:USERPROFILE)) { $scanPrefixes += $env:USERPROFILE }
$out = [IO.Path]::GetFullPath($Output)
$base = [IO.Path]::GetFullPath($PSScriptRoot).TrimEnd('\') + '\'
if (-not [IO.Path]::IsPathRooted($Output) -or -not $out.StartsWith($base,[StringComparison]::OrdinalIgnoreCase)) { throw 'Output must be inside the isolated installer work directory.' }
if (Test-Path -LiteralPath $out) { throw 'Existing installer retained.' }
if ((Get-FileHash -LiteralPath $manifest -Algorithm SHA256).Hash -ine $IntegritySha256) { throw 'The reviewed payload manifest changed.' }
$launcher = Get-Content -LiteralPath (Join-Path $stage 'tools\start-desktop.ps1') -Raw
if (-not $launcher.Contains($IntegritySha256.ToLowerInvariant())) { throw 'The launcher does not pin this integrity manifest.' }
$scanArgs = @((Join-Path $PSScriptRoot 'scan_payload.py'), $stage)
foreach ($prefix in $scanPrefixes) { $scanArgs += @('--private-prefix',$prefix) }
& (Join-Path $stage 'app\control\python\python.exe') -B @scanArgs
if ($LASTEXITCODE) { throw 'Privacy/model scan failed; installer not built.' }
& $Nsis "/DPAYLOAD=$stage" "/DOUTPUT=$out" "/DINTEGRITY_SHA256=$($IntegritySha256.ToLowerInvariant())" (Join-Path $PSScriptRoot 'setup.nsi')
if ($LASTEXITCODE) { throw 'NSIS build failed; inspect any partial output before retrying.' }
Get-FileHash -LiteralPath $out -Algorithm SHA256
