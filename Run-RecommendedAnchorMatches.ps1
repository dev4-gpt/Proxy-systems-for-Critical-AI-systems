<#
.SYNOPSIS
  Run Get-AnchorMatches.ps1 for every anchor in recommended_anchors_top.csv.

.EXAMPLE
  # Uses Get-AnchorMatches.ps1 defaults (MinimumScore 700, penalty 55, owner caps 2/1)
  pwsh ./Run-RecommendedAnchorMatches.ps1

.EXAMPLE
  # Override penalty for all anchors
  pwsh ./Run-RecommendedAnchorMatches.ps1 -CrossAnchorFreqPenaltyWeight 60

.EXAMPLE
  pwsh ./Run-RecommendedAnchorMatches.ps1 -SkipExisting -MaxAnchors 3
#>

[CmdletBinding()]
param(
    [string]$AnchorsCsv = "./recommended_anchors_top.csv",
    [string]$RunsDir = "runs/manual-ml-py",
    [int]$MaxAnchors = 0,
    [switch]$SkipExisting,
    [switch]$ResumePartial,

    # Optional — forwarded to Get-AnchorMatches.ps1 (omit to use that script's defaults)
    [string]$CrossAnchorRunsDir,
    [double]$CrossAnchorFreqPenaltyWeight,
    [int]$MaxPerOwner,
    [int]$MaxPerOwnerPerSubdomain,
    [switch]$DisableDiversityGuard,
    [int]$MinimumScore,
    [int]$TopK,
    [switch]$IncludeRetrievalSignalsInScore,
    [switch]$NoFallbackFill
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command not found: $Name"
    }
}

function Get-AnchorOutputFolder {
    param([string]$RepoName)
    $name = $RepoName.Trim()
    if ([string]::IsNullOrWhiteSpace($name)) { throw "Empty RepoName." }
    return ($name -replace '/', '-')
}

function Test-ManifestMatchesInvokeParams {
    param(
        [string]$OutputDir,
        [hashtable]$InvokeParams
    )
    $manifestPath = Join-Path $OutputDir "run_manifest.json"
    if (-not (Test-Path -LiteralPath $manifestPath)) { return $false }
    try {
        $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
        $saved = $manifest.params
    }
    catch { return $false }

    $checks = @(
        @{ Key = 'CrossAnchorFreqPenaltyWeight'; Saved = [double]$saved.CrossAnchorFreqPenaltyWeight },
        @{ Key = 'MinimumScore'; Saved = [int]$saved.MinimumScore },
        @{ Key = 'MaxPerOwner'; Saved = [int]$saved.MaxPerOwner },
        @{ Key = 'MaxPerOwnerPerSubdomain'; Saved = [int]$saved.MaxPerOwnerPerSubdomain }
    )
    foreach ($c in $checks) {
        if ($InvokeParams.ContainsKey($c.Key)) {
            if ([double]$InvokeParams[$c.Key] -ne [double]$c.Saved) { return $false }
        }
    }
    if ($InvokeParams.ContainsKey('AllowFallbackFill')) {
        $want = [bool]$InvokeParams.AllowFallbackFill
        $have = [bool]$saved.AllowFallbackFill
        if ($want -ne $have) { return $false }
    }
    return $true
}

Require-Command -Name "gh"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$matchScript = Join-Path $scriptDir "Get-AnchorMatches.ps1"
$anchorsPath = if ([System.IO.Path]::IsPathRooted($AnchorsCsv)) { $AnchorsCsv } else { Join-Path $scriptDir $AnchorsCsv }
$runsRoot = if ([System.IO.Path]::IsPathRooted($RunsDir)) { $RunsDir } else { Join-Path $scriptDir $RunsDir }

if (-not (Test-Path -LiteralPath $matchScript)) { throw "Missing script: $matchScript" }
if (-not (Test-Path -LiteralPath $anchorsPath)) { throw "Missing anchors CSV: $anchorsPath" }

New-Item -ItemType Directory -Path $runsRoot -Force | Out-Null

$rows = @(Import-Csv -LiteralPath $anchorsPath)
if ($MaxAnchors -gt 0) {
    $rows = @($rows | Select-Object -First $MaxAnchors)
}
if (@($rows).Count -eq 0) { throw "No anchors found in $anchorsPath" }

Write-Host "Anchors CSV: $anchorsPath" -ForegroundColor Cyan
Write-Host "Runs root:   $runsRoot" -ForegroundColor Cyan
Write-Host "Count:       $(@($rows).Count)" -ForegroundColor Cyan
if ($PSBoundParameters.Count -gt 4) {
    Write-Host "Extra Get-AnchorMatches params:" -ForegroundColor Gray
    foreach ($key in @(
        'CrossAnchorRunsDir','CrossAnchorFreqPenaltyWeight','MaxPerOwner','MaxPerOwnerPerSubdomain',
        'DisableDiversityGuard','MinimumScore','TopK','IncludeRetrievalSignalsInScore','NoFallbackFill'
    )) {
        if ($PSBoundParameters.ContainsKey($key)) {
            Write-Host ("  -{0} {1}" -f $key, $PSBoundParameters[$key]) -ForegroundColor Gray
        }
    }
}
Write-Host ""

$ok = 0
$skipped = 0
$failed = 0
$script:FailedAnchors = @()

foreach ($row in $rows) {
    $anchorRepo = [string]$row.RepoName
    if ([string]::IsNullOrWhiteSpace($anchorRepo)) { continue }

    $folder = Get-AnchorOutputFolder -RepoName $anchorRepo
    $outputDir = Join-Path $runsRoot $folder
    $finalCsv = Join-Path $outputDir "30_Matches.csv"

    $invokeParams = @{
        AnchorRepo = $anchorRepo
        OutputDir  = $outputDir
    }
    foreach ($key in @(
        'CrossAnchorRunsDir','CrossAnchorFreqPenaltyWeight','MaxPerOwner','MaxPerOwnerPerSubdomain',
        'DisableDiversityGuard','MinimumScore','TopK','IncludeRetrievalSignalsInScore'
    )) {
        if ($PSBoundParameters.ContainsKey($key)) {
            $invokeParams[$key] = $PSBoundParameters[$key]
        }
    }
    if ($NoFallbackFill) { $invokeParams.AllowFallbackFill = $false }

    if ((Test-Path -LiteralPath $finalCsv) -and ($SkipExisting -or $ResumePartial)) {
        if ((-not $ResumePartial) -or (Test-ManifestMatchesInvokeParams -OutputDir $outputDir -InvokeParams $invokeParams)) {
            Write-Host ("[{0}] SKIP (exists): {1}" -f $folder, $anchorRepo) -ForegroundColor Yellow
            $skipped++
            continue
        }
        if ($ResumePartial) {
            Write-Host ("[{0}] RE-RUN (params changed): {1}" -f $folder, $anchorRepo) -ForegroundColor Yellow
        }
    }

    Write-Host ("[{0}] RUN: {1}" -f $folder, $anchorRepo) -ForegroundColor Green
    try {
        & $matchScript @invokeParams
        $ok++
    }
    catch {
        Write-Host ("[{0}] FAILED: {1}" -f $folder, $_.Exception.Message) -ForegroundColor Red
        $script:FailedAnchors += ,[PSCustomObject]@{ Row = $row; Folder = $folder; Repo = $anchorRepo }
        $failed++
    }
    Write-Host ""
}

if ($script:FailedAnchors -and $script:FailedAnchors.Count -gt 0) {
    Write-Host "=== Retrying $($script:FailedAnchors.Count) failed anchor(s) after rate-limit cooldown ===" -ForegroundColor Yellow
    Start-Sleep -Seconds 90
    $retryFailed = @($script:FailedAnchors)
    $script:FailedAnchors = @()
    foreach ($item in $retryFailed) {
        $folder = $item.Folder
        $anchorRepo = $item.Repo
        $outputDir = Join-Path $runsRoot $folder
        Write-Host ("[{0}] RETRY: {1}" -f $folder, $anchorRepo) -ForegroundColor Cyan
        try {
            $invokeParams = @{ AnchorRepo = $anchorRepo; OutputDir = $outputDir }
            foreach ($key in @(
                'CrossAnchorRunsDir','CrossAnchorFreqPenaltyWeight','MaxPerOwner','MaxPerOwnerPerSubdomain',
                'DisableDiversityGuard','MinimumScore','TopK','IncludeRetrievalSignalsInScore'
            )) {
                if ($PSBoundParameters.ContainsKey($key)) { $invokeParams[$key] = $PSBoundParameters[$key] }
            }
            if ($NoFallbackFill) { $invokeParams.AllowFallbackFill = $false }
            & $matchScript @invokeParams
            $ok++
            $failed--
        }
        catch {
            Write-Host ("[{0}] RETRY FAILED: {1}" -f $folder, $_.Exception.Message) -ForegroundColor Red
        }
        Write-Host ""
    }
}

Write-Host "Done." -ForegroundColor Cyan
Write-Host ("  Ran:     {0}" -f $ok) -ForegroundColor Green
Write-Host ("  Skipped: {0}" -f $skipped) -ForegroundColor Yellow
Write-Host ("  Failed:  {0}" -f $failed) -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Gray" })

if ($failed -gt 0) { exit 1 }
exit 0
