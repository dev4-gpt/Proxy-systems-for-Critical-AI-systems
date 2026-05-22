<#
.SYNOPSIS
  Run all anchors (Get-AnchorMatches.ps1), summarize, evaluate, optionally archive and compare experiments.

.EXAMPLE
  pwsh ./Run-MetaMatchPipeline.ps1 -CrossAnchorFreqPenaltyWeight 75 `
    -ArchiveAsExperiment penalty75_min700_cap21 `
    -CompareWith penalty55_min700_cap21 penalty30_min700_cap21

.EXAMPLE
  pwsh ./Run-MetaMatchPipeline.ps1 -NoFallbackFill `
    -ArchiveAsExperiment penalty55_min700_cap21_nofallback `
    -CompareWith penalty55_min700_cap21

.EXAMPLE
  pwsh ./Run-MetaMatchPipeline.ps1 -SummarizeOnly
#>

[CmdletBinding()]
param(
    [switch]$SummarizeOnly,
    [switch]$SkipExisting,
    [switch]$ResumePartial,
    [int]$MaxAnchors = 0,
    [string]$AnchorsCsv = "./recommended_anchors_top.csv",
    [string]$RunsDir = "runs/manual-ml-py",
    [string]$ArchiveAsExperiment = "",
    [string[]]$CompareWith = @(),

    [ValidateSet('', 'penalty75', 'penalty100', 'min750', 'cap11', 'nofallback')]
    [string]$ExperimentPreset = '',

    [double]$CrossAnchorFreqPenaltyWeight = 0,
    [int]$MinimumScore = 0,
    [int]$MaxPerOwner = 0,
    [int]$MaxPerOwnerPerSubdomain = 0,
    [switch]$NoFallbackFill
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Presets avoid fragile hyperparam binding when pwsh is invoked from bash.
if ($ExperimentPreset) {
    switch ($ExperimentPreset) {
        'penalty75'  { $CrossAnchorFreqPenaltyWeight = 75 }
        'penalty100' { $CrossAnchorFreqPenaltyWeight = 100 }
        'min750'     { $MinimumScore = 750 }
        'cap11'      { $MaxPerOwner = 1 }
        'nofallback' { $NoFallbackFill = $true }
        default      { throw "Unknown ExperimentPreset: $ExperimentPreset" }
    }
}

function Build-ExperimentDescription {
    $parts = @()
    if ($CrossAnchorFreqPenaltyWeight -gt 0) {
        $parts += "penalty=$CrossAnchorFreqPenaltyWeight"
    }
    if ($MinimumScore -gt 0) {
        $parts += "minScore=$MinimumScore"
    }
    if ($MaxPerOwner -gt 0) {
        $parts += "maxOwner=$MaxPerOwner"
    }
    if ($MaxPerOwnerPerSubdomain -gt 0) {
        $parts += "maxOwnerSub=$MaxPerOwnerPerSubdomain"
    }
    if ($NoFallbackFill) { $parts += "fallback=off" }
    if ($parts.Count -eq 0) { return "MetaMatch pipeline (script defaults)" }
    return ($parts -join ", ")
}

function Get-TuningOverrides {
    $overrides = @{}
    if ($CrossAnchorFreqPenaltyWeight -gt 0) {
        $overrides.CrossAnchorFreqPenaltyWeight = $CrossAnchorFreqPenaltyWeight
    }
    if ($MinimumScore -gt 0) { $overrides.MinimumScore = $MinimumScore }
    if ($MaxPerOwner -gt 0) { $overrides.MaxPerOwner = $MaxPerOwner }
    if ($MaxPerOwnerPerSubdomain -gt 0) {
        $overrides.MaxPerOwnerPerSubdomain = $MaxPerOwnerPerSubdomain
    }
    if ($NoFallbackFill) { $overrides.NoFallbackFill = $true }
    return $overrides
}

if (-not $SummarizeOnly) {
    Write-Host "=== Step 0: Check gh ===" -ForegroundColor Cyan
    if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
        throw "GitHub CLI (gh) not found. Install and run: gh auth login"
    }
    gh auth status 2>&1 | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "gh not authenticated. Run: gh auth login -h github.com"
    }

    $batchParams = @{
        AnchorsCsv = $AnchorsCsv
        RunsDir    = $RunsDir
    }
    if ($SkipExisting) { $batchParams.SkipExisting = $true }
    if ($ResumePartial) { $batchParams.ResumePartial = $true }
    if ($MaxAnchors -gt 0) { $batchParams.MaxAnchors = $MaxAnchors }

    $batchParams += Get-TuningOverrides

    Write-Host "=== Step 1: Match all anchors ===" -ForegroundColor Cyan
    Write-Host ("  Params: {0}" -f (Build-ExperimentDescription)) -ForegroundColor Gray
    & (Join-Path $scriptDir "Run-RecommendedAnchorMatches.ps1") @batchParams
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Host "=== Step 2: Summarize + evaluation tables ===" -ForegroundColor Cyan
python3 tools/summarize_runs.py --runs-dir $RunsDir --topk 10 --evaluate
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if ($ArchiveAsExperiment) {
    Write-Host "=== Step 3: Archive experiment '$ArchiveAsExperiment' ===" -ForegroundColor Cyan
    $desc = Build-ExperimentDescription
    python3 tools/archive_experiment.py $ArchiveAsExperiment --description $desc --repo-root $scriptDir
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

if ($CompareWith.Count -gt 0 -and $ArchiveAsExperiment) {
    $allExps = @($CompareWith) + @($ArchiveAsExperiment)
    Write-Host "=== Step 4: Compare experiments ===" -ForegroundColor Cyan
    python3 tools/compare_experiments.py --experiments @allExps
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Host ""
Write-Host "Done." -ForegroundColor Green
Write-Host "  Live tables:     runs/_summaries/"
if ($ArchiveAsExperiment) {
    Write-Host "  Archive:         runs/experiments/$ArchiveAsExperiment/"
}
if ($CompareWith.Count -gt 0 -and $ArchiveAsExperiment) {
    Write-Host "  Comparison:      runs/experiments/experiment_comparison_summary.csv"
    Write-Host "                   runs/experiments/anchor_comparison_by_experiment.csv"
    Write-Host "                   runs/experiments/magnet_comparison_final30.csv"
}
