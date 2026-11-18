Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
try {
  $service = New-Object -ComObject 'Schedule.Service'
  $service.Connect()
  $folder = $service.GetFolder('\')
  try {
    $null = $folder.GetTask('Strata - startup')
    exit 1
  } catch {
    $code = [BitConverter]::ToUInt32([BitConverter]::GetBytes([int32]$_.Exception.HResult), 0)
    if ($code -eq [uint32]2147942402 -or $code -eq [uint32]2147943568) { exit 0 }
    exit 2
  }
} catch {
  # An unqueryable scheduler is not evidence that the old startup is absent.
  exit 2
}
