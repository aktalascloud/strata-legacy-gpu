$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$runtime = Join-Path $root 'runtime'
$readyFile = Join-Path $runtime 'ready.json'
$ready = Get-Content -LiteralPath $readyFile -Raw | ConvertFrom-Json
$ownerId = [int]$ready.pid
$owners = @(Get-NetTCPConnection -LocalPort $ready.bound_port -State Listen -ErrorAction SilentlyContinue)
if ($ready.instance_id -cnotmatch '^[A-Za-z0-9_-]{8,64}$' -or $ready.bound_host -ne '127.0.0.1' -or
    $owners.Count -ne 1 -or $owners[0].OwningProcess -ne $ownerId -or
    (Get-CimInstance Win32_Process -Filter "ProcessId=$ownerId").Name -ne 'python.exe') {
    throw 'Could not verify the Strata owner from this installation.'
}
$stopFile = Join-Path $runtime "stop-$($ready.instance_id)"
New-Item -Path $stopFile -ItemType File -Force | Out-Null
$deadline = [datetime]::UtcNow.AddMinutes(12)
do {
    Start-Sleep -Seconds 1
    $process = Get-Process -Id $ownerId -ErrorAction SilentlyContinue
} while ($process -and [datetime]::UtcNow -lt $deadline)
if ($process -or (Test-Path -LiteralPath $readyFile) -or
    (Get-NetTCPConnection -LocalPort $ready.bound_port -State Listen -ErrorAction SilentlyContinue)) {
    throw 'Strata has not finished shutting down.'
}
