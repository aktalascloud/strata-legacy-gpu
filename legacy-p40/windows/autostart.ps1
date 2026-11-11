param([switch]$Disable)
$ErrorActionPreference = 'Stop'
$key = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
$name = 'Strata Legacy GPU'
$worker = Join-Path $PSScriptRoot 'run-strata.ps1'
$shell = Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe'
$command = '"{0}" -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "{1}"' -f $shell, $worker
$current = Get-ItemPropertyValue -LiteralPath $key -Name $name -ErrorAction SilentlyContinue
if ($current -and $current -ne $command) { throw 'Another installation already owns this autostart entry.' }
if ($Disable) {
    if ($current) { Remove-ItemProperty -LiteralPath $key -Name $name }
} else {
    $config = Join-Path (Split-Path -Parent $PSScriptRoot) 'runtime\strata.json'
    if (-not (Test-Path -LiteralPath $config -PathType Leaf)) { throw 'Configure Swift before enabling autostart.' }
    New-ItemProperty -LiteralPath $key -Name $name -Value $command -PropertyType String -Force | Out-Null
    if ((Get-ItemPropertyValue -LiteralPath $key -Name $name) -cne $command) { throw 'Autostart readback failed.' }
}
