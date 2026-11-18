param(
  [Parameter(Mandatory)][string]$AppRoot,
  [Parameter(Mandatory)][string]$DesktopExe,
  [Parameter(Mandatory)][string]$HostRoot,
  [Parameter(Mandatory)][string]$ComponentRoot,
  [Parameter(Mandatory)][string]$CudaRoot,
  [Parameter(Mandatory)][string]$VisionRoot,
  [Parameter(Mandatory)][ValidatePattern('^[a-fA-F0-9]{64}$')][string]$DesktopSha256,
  [Parameter(Mandatory)][ValidatePattern('^[a-fA-F0-9]{64}$')][string]$ComponentManifestSha256,
  [Parameter(Mandatory)][string]$NodeLicense,
  [Parameter(Mandatory)][string]$VCRuntimeLicense,
  [Parameter(Mandatory)][string]$RustNotices,
  [Parameter(Mandatory)][string]$FrontendNotices,
  [Parameter(Mandatory)][string]$PonytailSkill,
  [Parameter(Mandatory)][string]$LicensesDir,
  [Parameter(Mandatory)][ValidateNotNullOrEmpty()][string[]]$PrivatePrefix
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$stage = Join-Path $PSScriptRoot 'payload'
if (Test-Path -LiteralPath $stage) { throw 'Payload directory already exists; it was retained.' }
foreach ($p in @($AppRoot,$DesktopExe,$HostRoot,$ComponentRoot,$CudaRoot,$VisionRoot,$NodeLicense,$VCRuntimeLicense,$RustNotices,$FrontendNotices,$PonytailSkill,$LicensesDir)) {
  if (-not [IO.Path]::IsPathRooted($p) -or -not (Test-Path -LiteralPath $p)) { throw "Missing absolute input: $p" }
}
if (@($PrivatePrefix | Where-Object { [string]::IsNullOrWhiteSpace($_) }).Count) { throw 'Private path prefixes must not be empty.' }
if (-not (Test-Path -LiteralPath $LicensesDir -PathType Container)) { throw 'LicensesDir must be a directory.' }
$scanPrefixes = @($PrivatePrefix) + @($PSScriptRoot,$AppRoot,$HostRoot,$ComponentRoot,$CudaRoot,$VisionRoot)
if (-not [string]::IsNullOrWhiteSpace($env:USERPROFILE)) { $scanPrefixes += $env:USERPROFILE }
$desktop = $DesktopExe
$manifest = Join-Path $ComponentRoot 'engine-component.json'
if ((Get-FileHash -LiteralPath $desktop -Algorithm SHA256).Hash -ine $DesktopSha256) { throw 'Desktop EXE does not match the selected build.' }
if ((Get-FileHash -LiteralPath $manifest -Algorithm SHA256).Hash -ine $ComponentManifestSha256) { throw 'Component manifest does not match the reviewed build.' }
$engine = Get-Content -LiteralPath $manifest -Raw | ConvertFrom-Json
if ($engine.id -ne 'strata-engine' -or $engine.backend -ne 'cuda' -or $engine.platform -ne 'windows-x86_64' -or $engine.entrypoint -ne 'strata.exe' -or 'sm_61' -notin $engine.archs) { throw 'Unexpected component architecture or identity.' }
$expected = @('strata.exe','strata_kq.dll','strata-vision.exe')
if (@($engine.files).Count -ne 3 -or @($engine.files | Where-Object { $_.path -notin $expected }).Count) { throw 'The component must contain exactly the reviewed engine, MMQ and vision executables.' }
foreach ($entry in $engine.files) {
  $file = Join-Path $ComponentRoot $entry.path
  if ((Get-Item -LiteralPath $file).Length -ne $entry.bytes -or (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash -ine $entry.sha256) { throw "Component mismatch: $($entry.path)" }
}
New-Item -ItemType Directory -Path $stage -ErrorAction Stop | Out-Null
function Copy-Tree([string]$from,[string]$to) {
  & robocopy.exe $from $to /E /XJ /XD __pycache__ test tests .git .venv /XF '*.pyc' '*.pyo' '*.pdb' '*.log' '*.map' 'expert-profile.bin' /NFL /NDL /NJH /NJS /NP | Out-Null
  if ($LASTEXITCODE -ge 8) { throw "Copy failed: $from" }
}
try {
  $appOut = Join-Path $stage 'app'
  New-Item -ItemType Directory -Path $appOut,(Join-Path $appOut 'host'),(Join-Path $stage 'tools'),(Join-Path $stage 'licenses'),(Join-Path $stage 'cuda'),(Join-Path $stage 'vision') -Force | Out-Null
  Copy-Item -LiteralPath $desktop -Destination $appOut
  foreach ($name in @('node','control','harness')) { Copy-Tree (Join-Path $AppRoot $name) (Join-Path $appOut $name) }
  foreach ($name in @('server','dist')) { Copy-Tree (Join-Path $HostRoot $name) (Join-Path $appOut "host\$name") }
  Copy-Item -LiteralPath (Join-Path $HostRoot 'package.json') -Destination (Join-Path $appOut 'host\package.json')
  $engineOut = Join-Path $stage ('components\engine\' + (Split-Path -Leaf $ComponentRoot))
  New-Item -ItemType Directory -Path $engineOut -Force | Out-Null
  Copy-Item -LiteralPath $manifest -Destination $engineOut
  $componentRecords = foreach ($entry in $engine.files) {
    $to = Join-Path $engineOut $entry.path
    Copy-Item -LiteralPath (Join-Path $ComponentRoot $entry.path) -Destination $to
    if ((Get-FileHash -LiteralPath $to -Algorithm SHA256).Hash -ine $entry.sha256) { throw "Component copy mismatch: $($entry.path)" }
    @{ path = ('components/engine/' + (Split-Path -Leaf $ComponentRoot) + '/' + $entry.path); sha256 = $entry.sha256.ToLowerInvariant() }
  }
  $externalRecords = foreach ($item in @(@('cuda',$CudaRoot,@('cudart64_12.dll','cublas64_12.dll','cublasLt64_12.dll')), @('vision',$VisionRoot,@('libomp.dll','MSVCP140_ATOMIC_WAIT.dll','MSVCP140.dll','VCOMP140.DLL','VCRUNTIME140_1.dll','VCRUNTIME140.dll')))) {
    foreach ($name in $item[2]) {
      $from = Join-Path $item[1] $name; $to = Join-Path (Join-Path $stage $item[0]) $name
      $digest = (Get-FileHash -LiteralPath $from -Algorithm SHA256).Hash.ToLowerInvariant()
      Copy-Item -LiteralPath $from -Destination $to
      if ((Get-FileHash -LiteralPath $to -Algorithm SHA256).Hash -ine $digest) { throw "Runtime DLL copy mismatch: $name" }
      @{ path = ($item[0] + '/' + $name); sha256 = $digest }
    }
  }
  $integrity = [ordered]@{ version=$engine.version; build_id=$engine.build_id; desktop_sha256=$DesktopSha256.ToLowerInvariant(); components=@($componentRecords); external=@($externalRecords) }
  $integrityPath = Join-Path $stage 'bundle-integrity.json'
  [IO.File]::WriteAllText($integrityPath, (ConvertTo-Json $integrity -Depth 8) + "`n", [Text.UTF8Encoding]::new($false))
  $hash = (Get-FileHash -LiteralPath $integrityPath -Algorithm SHA256).Hash.ToLowerInvariant()
  $launcher = [IO.File]::ReadAllText((Join-Path $PSScriptRoot 'start-desktop.ps1.in')).Replace('@@BUNDLE_HASH@@', $hash)
  [IO.File]::WriteAllText((Join-Path $stage 'tools\start-desktop.ps1'), $launcher, [Text.UTF8Encoding]::new($false))
  if ((Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'make_profile.py') -Algorithm SHA256).Hash -ine '39e522a03b8c95dd82bd87a0f03cd91ae660257d83ba0115a7a9a8ac297ec807') { throw 'Uniform-profile generator changed.' }
  foreach ($name in @('configure_profile.py','prepare_receipt.py','check-old-task.ps1','make_profile.py','install_skill.py')) { Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination (Join-Path $stage 'tools') }
  if ((Get-FileHash -LiteralPath $PonytailSkill -Algorithm SHA256).Hash -ine 'f18008471528f0adde90a560d053f85935eed5cee26c447b7177ad24472bcf32') { throw 'Ponytail skill differs from the reviewed MIT source.' }
  $skillDir = Join-Path $stage 'defaults\skills\ponytail'
  New-Item -ItemType Directory -Path $skillDir -Force | Out-Null
  Copy-Item -LiteralPath $PonytailSkill -Destination (Join-Path $skillDir 'SKILL.md')
  Copy-Tree $LicensesDir (Join-Path $stage 'licenses')
  Copy-Item -LiteralPath $NodeLicense -Destination (Join-Path $stage 'licenses\Node-LICENSE.txt')
  Copy-Item -LiteralPath $VCRuntimeLicense -Destination (Join-Path $stage 'licenses\Microsoft-VC-runtime-LICENSE.txt')
  Copy-Item -LiteralPath $RustNotices -Destination (Join-Path $stage 'licenses\Rust-third-party-notices.txt')
  Copy-Item -LiteralPath $FrontendNotices -Destination (Join-Path $stage 'licenses\Frontend-third-party-notices.txt')
  $scanArgs = @((Join-Path $PSScriptRoot 'scan_payload.py'), $stage)
  foreach ($prefix in $scanPrefixes) { $scanArgs += @('--private-prefix',$prefix) }
  & (Join-Path $AppRoot 'control\python\python.exe') -B @scanArgs
  if ($LASTEXITCODE) { throw 'Privacy/model scan failed; payload must not be shipped.' }
  Write-Output "Payload prepared. INTEGRITY_SHA256=$hash"
} catch {
  Write-Error "Payload not accepted; stage retained for inspection: $stage. $($_.Exception.Message)"
  throw
}
