param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [int[]]$Ports
)

if (-not $Ports -or $Ports.Count -eq 0) {
    exit 0
}

$allPids = @()

foreach ($port in $Ports) {
    try {
        $pids = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction Stop |
            Select-Object -ExpandProperty OwningProcess -Unique
        if ($pids) {
            $allPids += $pids
        }
    }
    catch {
        # Ignore ports without listeners.
    }
}

$allPids = $allPids | Sort-Object -Unique

foreach ($procId in $allPids) {
    try {
        Stop-Process -Id $procId -Force -ErrorAction Stop
        Write-Output "Stopped process $procId"
    }
    catch {
        # Ignore processes that already exited.
    }
}
