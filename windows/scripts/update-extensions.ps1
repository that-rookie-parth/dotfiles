# update-extensions.ps1
#
# Updates VS Code extensions only if the latest version has been out for at least
# $DaysThreshold days. Handles both local (Windows) and WSL extensions.
#
# Usage:
#   .\update-extensions.ps1                  # uses default 7-day threshold
#   .\update-extensions.ps1 -DaysThreshold 14

param(
    [int]$DaysThreshold = 7
)

$scriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$localFile  = Join-Path $scriptDir "..\vscode\extensions-local.txt"
$wslFile    = Join-Path $scriptDir "..\vscode\extensions-wsl.txt"

# ---------------------------------------------------------------------------
# Query the VS Code Marketplace for the latest version and its release date
# ---------------------------------------------------------------------------
function Get-ExtensionInfo {
    param([string]$ExtensionId)

    $body = @{
        filters = @(@{
            criteria = @(@{ filterType = 7; value = $ExtensionId })
        })
        flags = 512
    } | ConvertTo-Json -Depth 5

    try {
        $response = Invoke-RestMethod `
            -Uri     "https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery" `
            -Method  POST `
            -Headers @{ Accept = "application/json;api-version=3.0-preview.1" } `
            -ContentType "application/json" `
            -Body    $body

        $latest = $response.results[0].extensions[0].versions[0]
        return @{
            Version     = $latest.version
            ReleaseDate = [DateTime]$latest.lastUpdated
            AgeDays     = ([DateTime]::UtcNow - [DateTime]$latest.lastUpdated).Days
        }
    }
    catch {
        return $null
    }
}

# ---------------------------------------------------------------------------
# Process one extension list
# ---------------------------------------------------------------------------
function Update-ExtensionList {
    param(
        [string]$ExtFile,
        [string]$Target,      # "local" or "wsl"
        [int]   $Threshold
    )

    if (-not (Test-Path $ExtFile)) {
        Write-Host "  [skip] file not found: $ExtFile" -ForegroundColor DarkYellow
        return
    }

    $extensions = Get-Content $ExtFile |
        Where-Object { $_ -match '\S' -and $_ -notmatch '^\s*#' } |
        ForEach-Object { $_.Trim() }

    foreach ($ext in $extensions) {
        Write-Host -NoNewline "  $ext ... "

        $info = Get-ExtensionInfo -ExtensionId $ext

        if ($null -eq $info) {
            Write-Host "could not reach marketplace" -ForegroundColor Red
            continue
        }

        if ($info.AgeDays -ge $Threshold) {
            Write-Host "v$($info.Version) | $($info.AgeDays)d old -> UPDATING" -ForegroundColor Green

            if ($Target -eq "local") {
                code --install-extension $ext --force 2>&1 | Out-Null
            }
            else {
                # Runs code from inside WSL so the extension installs on the WSL side
                wsl -d Ubuntu -- bash -c "code --install-extension '$ext' --force 2>/dev/null"
            }
        }
        else {
            $daysLeft = $Threshold - $info.AgeDays
            Write-Host "v$($info.Version) | $($info.AgeDays)d old -> SKIP ($daysLeft days left)" -ForegroundColor Yellow
        }
    }
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "VS Code Extension Updater  (threshold: $DaysThreshold days)" -ForegroundColor Cyan
Write-Host ""

Write-Host "LOCAL extensions (Windows):" -ForegroundColor White
Update-ExtensionList -ExtFile $localFile -Target "local" -Threshold $DaysThreshold

Write-Host ""
Write-Host "WSL extensions (Ubuntu):" -ForegroundColor White
Update-ExtensionList -ExtFile $wslFile -Target "wsl" -Threshold $DaysThreshold

Write-Host ""
Write-Host "Done." -ForegroundColor Cyan
