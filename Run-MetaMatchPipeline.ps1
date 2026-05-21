<#
.SYNOPSIS
  Run all anchors (Get-AnchorMatches.ps1 defaults), summarize, evaluate, optionally archive and compare experiments.

.EXAMPLE
  pwsh ./Run-MetaMatchPipeline.ps1 -ArchiveAsExperiment penalty55_min700_cap21

.EXAMPLE
  pwsh ./Run-MetaMatchPipeline.ps1 -SummarizeOnly

.EXAMPLE
  pwsh ./Run-MetaMatchPipeline.ps1 -ArchiveAsExperiment penalty55_min700_cap21 -CompareWith penalty30_min700_cap21
#>

[CmdletBinding()]
param(
    [switch]$SummarizeOnly,
    [switch]$SkipExisting,
    [int]$MaxAnchors = 0,
    [string]$AnchorsCsv = "./recommended_anchors_top.csv",
    [string]$RunsDir = "runs/manual-ml-py",
    [string]$ArchiveAsExperiment = "",
    [string[]]$CompareWith = @()
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

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
    if ($MaxAnchors -gt 0) { $batchParams.MaxAnchors = $MaxAnchors }

    Write-Host "=== Step 1: Match all anchors (Get-AnchorMatches.ps1 defaults) ===" -ForegroundColor Cyan
    & (Join-Path $scriptDir "Run-RecommendedAnchorMatches.ps1") @batchParams
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Host "=== Step 2: Summarize + evaluation tables ===" -ForegroundColor Cyan
python3 tools/summarize_runs.py --runs-dir $RunsDir --topk 10 --evaluate
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if ($ArchiveAsExperiment) {
    Write-Host "=== Step 3: Archive experiment '$ArchiveAsExperiment' ===" -ForegroundColor Cyan
    $desc = "MetaMatch run archived after pipeline (see run_hyperparams.csv in folder)"
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
