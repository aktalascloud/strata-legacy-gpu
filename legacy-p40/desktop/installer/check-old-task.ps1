Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
try {
  Import-Module (Join-Path $PSHOME 'Modules\Microsoft.PowerShell.Utility\Microsoft.PowerShell.Utility.psd1')
  $service = New-Object -ComObject 'Schedule.Service'
  $service.Connect()
  $folder = $service.GetFolder('\')
  try {
    $task = $folder.GetTask('Strata - startup')
    if ($task.Enabled) { exit 1 }
    exit 0
  } catch {
    $code = [BitConverter]::ToUInt32([BitConverter]::GetBytes([int32]$_.Exception.HResult), 0)
    if ($code -eq [uint32]2147942402 -or $code -eq [uint32]2147943568) { exit 0 }
    exit 2
  }
} catch {
  # An unqueryable scheduler is not evidence that the old startup is absent.
  exit 2
}
