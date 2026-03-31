# Update Dashboard with Run Timestamp
# This script updates the Dashboard.md with the current run timestamp

$dashboardPath = Join-Path $PSScriptRoot "Hydrology-Vault\Dashboard.md"
$logPath = Join-Path $PSScriptRoot "Hydrology-Vault\agent_log.txt"

if (Test-Path $dashboardPath) {
    $currentTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $content = Get-Content $dashboardPath -Raw
    
    # Update Last Run - find the line and replace the value
    $lines = $content -split "`n"
    $currentRuns = 0
    $foundRuns = $false
    
    for ($i = 0; $i -lt $lines.Length; $i++) {
        if ($lines[$i] -match '\*\*Last Run:\*\*') {
            $lines[$i] = "**Last Run:** $currentTime"
        }
        if ($lines[$i] -match '\*\*Total Runs:\*\* (\d+)') {
            # Extract current count
            $currentRuns = [int]$matches[1]
            $foundRuns = $true
        }
        if ($lines[$i] -match '\*\*Next Scheduled Run:\*\*') {
            $nextRun = (Get-Date).AddDays(1).Date.AddHours(8)
            $nextRunStr = $nextRun.ToString("yyyy-MM-dd HH:mm")
            $lines[$i] = "**Next Scheduled Run:** $nextRunStr"
        }
    }
    
    # Increment runs and update
    if ($foundRuns) {
        $newRuns = $currentRuns + 1
    } else {
        $newRuns = 1
    }
    
    # Update Total Runs line
    for ($i = 0; $i -lt $lines.Length; $i++) {
        if ($lines[$i] -match '\*\*Total Runs:\*\*') {
            $lines[$i] = "**Total Runs:** $newRuns"
            break
        }
    }
    
    # Rejoin lines
    $content = $lines -join "`n"
    
    # Update Quick Stats Total Agent Runs
    $content = $content -replace '(\| Total Agent Runs \|) \d+', "`$1 $newRuns"
    
    Set-Content -Path $dashboardPath -Value $content -NoNewline
    
    Write-Host "Dashboard updated: Last Run = $currentTime, Total Runs = $newRuns"
    
    # Also log to agent_log.txt
    if (Test-Path $logPath) {
        Add-Content -Path $logPath -Value "Dashboard updated: Last Run = $currentTime, Total Runs = $newRuns`n"
    }
} else {
    Write-Host "Dashboard.md not found at: $dashboardPath"
}
