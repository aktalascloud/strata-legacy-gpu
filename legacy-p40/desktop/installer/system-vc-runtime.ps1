param([string]$Destination)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$minimum = [version]'14.51.36247.0'
$names = @('MSVCP140_ATOMIC_WAIT.dll', 'MSVCP140.dll', 'VCOMP140.DLL', 'VCRUNTIME140_1.dll', 'VCRUNTIME140.dll')
if (-not [Environment]::Is64BitProcess) { throw 'Use 64-bit PowerShell to locate the x64 Microsoft runtime.' }
Import-Module (Join-Path $PSHOME 'Modules\Microsoft.PowerShell.Security\Microsoft.PowerShell.Security.psd1')

$files = foreach ($name in $names) {
  $source = Join-Path $env:WINDIR "System32\$name"
  if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "Missing Microsoft runtime file: $name" }
  $info = [Diagnostics.FileVersionInfo]::GetVersionInfo($source)
  $version = [version]::new($info.FileMajorPart, $info.FileMinorPart, $info.FileBuildPart, $info.FilePrivatePart)
  $signature = Get-AuthenticodeSignature -LiteralPath $source
  if ($version -lt $minimum -or $signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch '\bMicrosoft Corporation\b') {
    throw "Expected a current Microsoft-signed x64 runtime file: $name"
  }
  $source
}

if ($Destination) {
  $target = (Resolve-Path -LiteralPath $Destination).Path
  foreach ($file in $files) {
    [IO.File]::Copy($file, (Join-Path $target (Split-Path -Leaf $file)), $false)
  }
}
