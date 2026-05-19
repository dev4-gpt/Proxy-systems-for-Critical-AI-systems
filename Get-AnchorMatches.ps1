<#
.SYNOPSIS
  Find up to TopK repositories that may match a single anchor repository.

.DESCRIPTION
  Uses GitHub's REST search API through `gh api` to:
    1) fetch anchor repository metadata
    2) derive search queries from the anchor's topics, language, name, and description
    3) retrieve a broad candidate pool
    4) score and rank candidates against the anchor
    5) write ranked_matches.csv and 30_Matches.csv, plus a run_manifest.json (MetaMatch 2.0)

KEY METAIMPROVEMENTS (MetaMatch 2.0)
  - Explainability columns in ranked_matches.csv:
      ScoreBreakdownJson, TopSignals, WhyQualified, PenaltyCrossAnchorFreq, PenaltyRetrieval, PenaltyNotes
  - Retrieval signals (QueryCoverage) are NOT part of similarity score by default.
      Use -IncludeRetrievalSignalsInScore to opt in.
  - Optional cross-anchor "magnet" penalty to improve diversity across anchors.
      Use -CrossAnchorFreqPenaltyWeight (0=off).
  - Diversity guard knobs to prevent a single owner/org from dominating TopK:
      -MaxPerOwner (global) and -MaxPerOwnerPerSubdomain (per subdomain bucket)

.PARAMETER AnchorRepo
  GitHub repo as owner/repo or full URL (https://github.com/owner/repo)

.PARAMETER OutputDir
  Directory for output files. Defaults to current directory.

.PARAMETER TopK
  Number of final matches to emit. Defaults to 30.

.PARAMETER MaxSearchPerQuery
  Number of search results per query. Defaults to 50.

.PARAMETER MinimumStars
  Minimum stars for candidate repos. Defaults to 50.

.PARAMETER MinimumScore
  Minimum weighted similarity score to qualify. Defaults to 900.

.PARAMETER IncludeRetrievalSignalsInScore
  If set, QueryCoverage contributes to Score. Default is off (recommended) to avoid retrieval artifacts.

.PARAMETER CrossAnchorRunsDir
  Directory that contains prior anchor run folders (default: runs/manual-ml-py).
  Used only if CrossAnchorFreqPenaltyWeight > 0.

.PARAMETER CrossAnchorFreqPenaltyWeight
  Optional penalty weight applied to frequent candidates across prior anchors.
  Default 0 (off). When enabled, the score is reduced by:
      weight * log10(1 + frequency)
  This is a light-touch "magnet repo" guard to improve diversity across anchors.

.PARAMETER MaxPerOwner
  Diversity cap: max results per owner/org in TopK. Default 3.

.PARAMETER MaxPerOwnerPerSubdomain
  Diversity cap: max results per owner WITHIN a subdomain bucket in TopK. Default 2.
  Set to 0 to disable this cap.

.PARAMETER DisableDiversityGuard
  Disable all diversity caps.

.PARAMETER AllowSameOwner
  Allow matches from same owner/org as anchor. Default false.

.PARAMETER AllowForks
  Allow fork repos. Default false.

.PARAMETER AllowArchived
  Allow archived repos. Default false.

.PARAMETER AllowFallbackFill
  If fewer than TopK repos exceed MinimumScore, fill remaining slots from next best candidates. Default true.

.NOTES
  Requires:
    - gh CLI installed and authenticated
    - PowerShell 5.1+ or PowerShell 7+
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$AnchorRepo,

    [string]$OutputDir = ".",

    [int]$TopK = 30,

    [int]$MaxSearchPerQuery = 50,

    [int]$MinimumStars = 50,

    [int]$MinimumScore = 900,

    [switch]$IncludeRetrievalSignalsInScore,

    [string]$CrossAnchorRunsDir = "runs/manual-ml-py",

    [double]$CrossAnchorFreqPenaltyWeight = 150.0,

    [int]$MaxPerOwner = 2,

    [int]$MaxPerOwnerPerSubdomain = 2,

    [switch]$DisableDiversityGuard,

    [switch]$AllowSameOwner,

    [switch]$AllowForks,

    [switch]$AllowArchived,

    [switch]$AllowFallbackFill = $true
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Scoring weights (tune here). Persisted to run_manifest.json for reproducibility.
# NOTE: QueryCoverage is a retrieval-confidence signal; it is NOT part of similarity score by default.
$ScoreWeights = @{
    TopicJaccard      = 900.0
    LexicalJaccard    = 650.0
    LanguageMatch     = 250.0
    StarSimilarity    = 175.0
    RecencySimilarity = 125.0
    SubdomainMatch    = 225.0
    QueryCoverage     = 150.0  # only used if -IncludeRetrievalSignalsInScore
}

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command not found: $Name"
    }
}

function Normalize-AnchorRepo {
    param([string]$InputRepo)
    $repo = $InputRepo.Trim()
    if ($repo -match '^https?://github\.com/([^/]+)/([^/#?]+)') { return "$($Matches[1])/$($Matches[2])" }
    if ($repo -match '^[^/]+/[^/]+$') { return $repo }
    throw "AnchorRepo must be owner/repo or a full GitHub URL."
}

function Get-Json {
    param([string]$Text)
    if ([string]::IsNullOrWhiteSpace($Text)) { return $null }
    return $Text | ConvertFrom-Json
}

function Invoke-GhApi {
    param([string]$Path, [hashtable]$Fields = @{})
    $args = @("api", "-X", "GET", $Path)
    foreach ($key in $Fields.Keys) { $args += @("-f", "$key=$($Fields[$key])") }
    $raw = & gh @args 2>&1
    if ($LASTEXITCODE -ne 0) { throw "gh api failed for path '$Path': $raw" }
    return Get-Json -Text $raw
}

function Get-RepoDetails {
    param([string]$FullName)
    $repo = Invoke-GhApi -Path ("repos/{0}" -f $FullName)
    return [PSCustomObject]@{
        FullName    = [string]$repo.full_name
        Name        = [string]$repo.name
        Url         = [string]$repo.html_url
        Description = [string]$repo.description
        Topics      = @($repo.topics)
        Language    = [string]$repo.language
        Stars       = [int]$repo.stargazers_count
        Fork        = [bool]$repo.fork
        Archived    = [bool]$repo.archived
        CreatedAt   = [datetime]$repo.created_at
        UpdatedAt   = [datetime]$repo.updated_at
        Owner       = [string]$repo.owner.login
    }
}

function Search-Repositories {
    param([string]$Query, [int]$PerPage = 50)
    Write-Host "Searching: $Query" -ForegroundColor Gray
    $resp = Invoke-GhApi -Path "search/repositories" -Fields @{ q=$Query; sort="stars"; order="desc"; per_page=$PerPage }
    $items = @($resp.items)
    Write-Host "  Found $(@($items).Count) repositories." -ForegroundColor Green
    return $items
}

function Get-TextTokens {
    param([string]$Text)
    if ([string]::IsNullOrWhiteSpace($Text)) { return @() }
    $stop = @(
        "the","and","for","with","from","into","using","based","tool","repo","repository",
        "project","system","software","application","framework","library","package","code",
        "python","javascript","typescript","java","rust","csharp","cpp","go","php","ruby",
        "an","a","to","of","in","on","at","by","or","is","are","this","that","it","be"
    ) | ForEach-Object { $_.ToLowerInvariant() }
    $parts = ($Text.ToLowerInvariant() -replace '[^a-z0-9\-\+ ]', ' ') -split '\s+'
    $parts = $parts | Where-Object { $_ -and $_.Length -ge 3 -and ($stop -notcontains $_) }
    return @($parts | Select-Object -Unique)
}

function Get-RepoLexicalTokens {
    param([object]$Repo)
    $nameTokens = Get-TextTokens -Text ([string]$Repo.Name -replace '[-_]', ' ')
    $descTokens = Get-TextTokens -Text ([string]$Repo.Description)
    return @($nameTokens + $descTokens | Select-Object -Unique)
}

function Compute-Jaccard {
    param([string[]]$A, [string[]]$B)
    $setA = [System.Collections.Generic.HashSet[string]]::new()
    foreach ($item in @($A)) {
        if ($null -eq $item) { continue }
        $value = [string]$item
        if (-not [string]::IsNullOrWhiteSpace($value)) { [void]$setA.Add($value.ToLowerInvariant()) }
    }
    $setB = [System.Collections.Generic.HashSet[string]]::new()
    foreach ($item in @($B)) {
        if ($null -eq $item) { continue }
        $value = [string]$item
        if (-not [string]::IsNullOrWhiteSpace($value)) { [void]$setB.Add($value.ToLowerInvariant()) }
    }
    if ($setA.Count -eq 0 -and $setB.Count -eq 0) { return 0.0 }
    $inter = 0
    foreach ($x in $setA) { if ($setB.Contains($x)) { $inter++ } }
    $union = $setA.Count + $setB.Count - $inter
    if ($union -le 0) { return 0.0 }
    return [double]$inter / [double]$union
}

function Get-Subdomain {
    param([string]$Description, [string[]]$Topics, [string]$Language)
    $text = ((@($Topics) -join " ") + " " + [string]$Description + " " + [string]$Language).ToLowerInvariant()
    $rules = [ordered]@{
        "llm"             = @("llm","gpt","transformer","instruction","rag","prompt","chatbot","language-model")
        "deep-learning"   = @("deep-learning","neural","cnn","rnn","torch","tensorflow","keras")
        "computer-vision" = @("computer-vision","image","vision","detection","segmentation","ocr","opencv")
        "nlp"             = @("nlp","natural-language","tokenization","embedding","summarization","translation")
        "mlops"           = @("mlops","pipeline","orchestration","serving","deployment","tracking","experiment")
        "editor"          = @("editor","ide","code-editor","text-editor","syntax-highlighting","lsp","language-server")
        "data-science"    = @("data-science","notebook","analysis","feature-engineering","pandas","sklearn")
        "reinforcement"   = @("reinforcement","rl","policy","agent","gym")
    }
    foreach ($key in $rules.Keys) {
        foreach ($needle in $rules[$key]) { if ($text -like "*$needle*") { return $key } }
    }
    return ""
}

function New-SearchQueriesFromAnchor {
    param([object]$Anchor)
    $queries = [System.Collections.Generic.List[string]]::new()
    $topicList = @($Anchor.Topics | Where-Object { $_ -and $_.Trim() } | Select-Object -First 5)
    $lang = [string]$Anchor.Language
    $nameTokens = Get-TextTokens -Text ([string]$Anchor.Name -replace '[-_]', ' ')
    $descTokens = Get-TextTokens -Text ([string]$Anchor.Description)

    if (@($topicList).Count -gt 0 -and $lang) { $queries.Add(("topic:{0} language:{1} stars:>={2}" -f $topicList[0], $lang, $MinimumStars)) }
    foreach ($t in ($topicList | Select-Object -First 3)) {
        if ($lang) { $queries.Add(("topic:{0} language:{1} stars:>={2}" -f $t, $lang, $MinimumStars)) }
        else { $queries.Add(("topic:{0} stars:>={1}" -f $t, $MinimumStars)) }
    }
    if (@($descTokens).Count -gt 0 -and $lang) { $queries.Add(("{0} language:{1} stars:>={2}" -f $descTokens[0], $lang, $MinimumStars)) }
    if (@($nameTokens).Count -gt 0 -and $lang) { $queries.Add(("{0} language:{1} stars:>={2}" -f $nameTokens[0], $lang, $MinimumStars)) }

    $sub = Get-Subdomain -Description $Anchor.Description -Topics $Anchor.Topics -Language $Anchor.Language
    switch ($sub) {
        "llm"             { $queries.Add("topic:llm stars:>=100") }
        "deep-learning"   { $queries.Add("topic:deep-learning stars:>=100") }
        "computer-vision" { $queries.Add("topic:computer-vision stars:>=100") }
        "nlp"             { $queries.Add("topic:nlp stars:>=100") }
        "mlops"           { $queries.Add("topic:mlops stars:>=100") }
        "editor"          { $queries.Add("topic:editor stars:>=100") }
        "data-science"    { $queries.Add("topic:data-science stars:>=100") }
        "reinforcement"   { $queries.Add("reinforcement learning stars:>=100") }
    }
    return @($queries | Where-Object { $_ -and $_.Trim() } | Select-Object -Unique)
}

function Test-JunkRepo {
    param([object]$Repo)
    $text = ("{0} {1}" -f [string]$Repo.FullName, [string]$Repo.Description).ToLowerInvariant()
    $junkPatterns = @("awesome","tutorial","boilerplate","template","starter","snippets","sandbox","notes","roadmap","interview","cheatsheet","curated-list","book","course","examples")
    foreach ($p in $junkPatterns) { if ($text -like "*$p*") { return $true } }
    return $false
}

function Get-StarSimilarity {
    param([int]$AnchorStars, [int]$CandidateStars)
    if ($AnchorStars -le 0 -or $CandidateStars -le 0) { return 0.0 }
    $a = [math]::Log10([double]($AnchorStars + 1))
    $b = [math]::Log10([double]($CandidateStars + 1))
    $delta = [math]::Abs($a - $b)
    return [math]::Max(0.0, 1.0 - ($delta / 2.0))
}

function Get-RecencySimilarity {
    param([datetime]$AnchorUpdated, [datetime]$CandidateUpdated)
    $days = [math]::Abs(($AnchorUpdated - $CandidateUpdated).TotalDays)
    if ($days -le 30)  { return 1.0 }
    if ($days -le 90)  { return 0.8 }
    if ($days -le 180) { return 0.6 }
    if ($days -le 365) { return 0.4 }
    return 0.2
}

function Get-CrossAnchorFrequencyMap {
    param([string]$RunsDir, [string]$CurrentAnchorFullName)

    # Why: "magnet repos" (popular/foundation libs) can appear in many anchors and dominate.
    # This optional map allows a gentle penalty for highly recurrent candidates.
    $map = @{}
    if (-not (Test-Path -LiteralPath $RunsDir)) { return $map }

    $files = Get-ChildItem -Path $RunsDir -Recurse -Filter "ranked_matches.csv" -ErrorAction SilentlyContinue
    foreach ($f in $files) {
        try {
            $rows = Import-Csv -LiteralPath $f.FullName
        } catch { continue }
        foreach ($r in $rows) {
            $a = [string]$r.AnchorRepo
            if ($a -and $a.ToLowerInvariant() -eq $CurrentAnchorFullName.ToLowerInvariant()) { continue }
            $c = [string]$r.CandidateRepo
            if (-not $c) { continue }
            if (-not $map.ContainsKey($c)) { $map[$c] = 0 }
            $map[$c] = [int]$map[$c] + 1
        }
    }
    return $map
}

function Score-Candidate {
    param([object]$Anchor, [object]$Candidate, [string[]]$MatchedQueries, [hashtable]$CrossAnchorFreq)

    $anchorTopics = @($Anchor.Topics)
    $candTopics = @($Candidate.Topics)
    $anchorLex = Get-RepoLexicalTokens -Repo $Anchor
    $candLex = Get-RepoLexicalTokens -Repo $Candidate

    $topicJ = Compute-Jaccard -A $anchorTopics -B $candTopics
    $lexJ = Compute-Jaccard -A $anchorLex -B $candLex

    $langMatch = if ($Anchor.Language -and $Candidate.Language -and $Anchor.Language.ToLowerInvariant() -eq $Candidate.Language.ToLowerInvariant()) { 1.0 } else { 0.0 }
    $starSim = Get-StarSimilarity -AnchorStars $Anchor.Stars -CandidateStars $Candidate.Stars
    $recencySim = Get-RecencySimilarity -AnchorUpdated $Anchor.UpdatedAt -CandidateUpdated $Candidate.UpdatedAt

    $anchorSub = Get-Subdomain -Description $Anchor.Description -Topics $Anchor.Topics -Language $Anchor.Language
    $candSub = Get-Subdomain -Description $Candidate.Description -Topics $Candidate.Topics -Language $Candidate.Language
    $subdomainMatch = if ($anchorSub -and $candSub -and $anchorSub -eq $candSub) { 1.0 } else { 0.0 }

    # Retrieval confidence (diagnostic). Avoid mixing "how we found it" into similarity by default.
    $queryCoverage = [math]::Min(1.0, [double](@($MatchedQueries).Count) / 3.0)

    # Base contributions
    $cTopic = ($ScoreWeights.TopicJaccard      * $topicJ)
    $cLex   = ($ScoreWeights.LexicalJaccard    * $lexJ)
    $cLang  = ($ScoreWeights.LanguageMatch     * $langMatch)
    $cStar  = ($ScoreWeights.StarSimilarity    * $starSim)
    $cRec   = ($ScoreWeights.RecencySimilarity * $recencySim)
    $cSub   = ($ScoreWeights.SubdomainMatch    * $subdomainMatch)

    $cRetr  = 0.0
    if ($IncludeRetrievalSignalsInScore) {
        $cRetr = ($ScoreWeights.QueryCoverage * $queryCoverage)
    }

    $scoreBase = $cTopic + $cLex + $cLang + $cStar + $cRec + $cSub + $cRetr

    # Optional cross-anchor magnet penalty: penalize frequent candidates across prior anchors.
    $freq = 0
    if ($CrossAnchorFreqPenaltyWeight -gt 0.0 -and $CrossAnchorFreq -and $CrossAnchorFreq.ContainsKey($Candidate.FullName)) {
        $freq = [int]$CrossAnchorFreq[$Candidate.FullName]
    }
    $penFreq = 0.0
    if ($freq -gt 0 -and $CrossAnchorFreqPenaltyWeight -gt 0.0) {
        $penFreq = $CrossAnchorFreqPenaltyWeight * [math]::Log10(1.0 + [double]$freq)
    }

    $scoreFinal = [math]::Max(0.0, $scoreBase - $penFreq)

    # Explainability: top contributing positive signals
    $pairs = @(
        @{k="Topic"; v=$cTopic},
        @{k="Lexical"; v=$cLex},
        @{k="Lang"; v=$cLang},
        @{k="Stars"; v=$cStar},
        @{k="Recency"; v=$cRec},
        @{k="Subdomain"; v=$cSub}
    )
    if ($IncludeRetrievalSignalsInScore) { $pairs += @{k="Retrieval"; v=$cRetr} }
    $top = @($pairs | Sort-Object -Property @{Expression={$_.v};Descending=$true} | Select-Object -First 3 | ForEach-Object { $_.k })

    $breakdown = [ordered]@{
        Topic=$([math]::Round($cTopic,2))
        Lexical=$([math]::Round($cLex,2))
        Lang=$([math]::Round($cLang,2))
        Stars=$([math]::Round($cStar,2))
        Recency=$([math]::Round($cRec,2))
        Subdomain=$([math]::Round($cSub,2))
        Retrieval=$([math]::Round($cRetr,2))
        PenaltyCrossAnchorFreq=$([math]::Round($penFreq,2))
        ScoreBase=$([math]::Round($scoreBase,2))
        ScoreFinal=$([math]::Round($scoreFinal,2))
    }

    return [PSCustomObject]@{
        TopicJaccard      = [math]::Round($topicJ, 4)
        LexicalJaccard    = [math]::Round($lexJ, 4)
        LanguageMatch     = [math]::Round($langMatch, 4)
        StarSimilarity    = [math]::Round($starSim, 4)
        RecencySimilarity = [math]::Round($recencySim, 4)
        SubdomainMatch    = [math]::Round($subdomainMatch, 4)
        QueryCoverage     = [math]::Round($queryCoverage, 4)
        AnchorSubdomain   = $anchorSub
        CandidateSubdomain= $candSub
        Score             = [math]::Round($scoreFinal, 2)
        ScoreBase         = [math]::Round($scoreBase, 2)
        PenaltyCrossAnchorFreq = [math]::Round($penFreq, 2)
        TopSignals        = ($top -join "+")
        ScoreBreakdownJson= ($breakdown | ConvertTo-Json -Compress)
    }
}

Require-Command -Name "gh"

$OutputDir = [System.IO.Path]::GetFullPath($OutputDir)
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

$anchorFullName = Normalize-AnchorRepo -InputRepo $AnchorRepo
Write-Host "Anchor: $anchorFullName" -ForegroundColor Cyan

$anchor = Get-RepoDetails -FullName $anchorFullName

$anchorObj = [PSCustomObject]@{
    FullName    = $anchor.FullName
    Name        = $anchor.Name
    Url         = $anchor.Url
    Description = $anchor.Description
    Topics      = @($anchor.Topics)
    Language    = $anchor.Language
    Stars       = $anchor.Stars
    Fork        = $anchor.Fork
    Archived    = $anchor.Archived
    CreatedAt   = $anchor.CreatedAt
    UpdatedAt   = $anchor.UpdatedAt
    Owner       = $anchor.Owner
}

$searchQueries = New-SearchQueriesFromAnchor -Anchor $anchorObj
if (@($searchQueries).Count -eq 0) { throw "Could not derive any search queries from the anchor repository." }

# Optional: cross-anchor frequency map (only computed if penalty enabled)
$freqMap = @{}
if ($CrossAnchorFreqPenaltyWeight -gt 0.0) {
    $freqMap = Get-CrossAnchorFrequencyMap -RunsDir $CrossAnchorRunsDir -CurrentAnchorFullName $anchorObj.FullName
}

$candidateMap = @{}

foreach ($query in $searchQueries) {
    $results = Search-Repositories -Query $query -PerPage $MaxSearchPerQuery

    foreach ($repo in $results) {
        $fullName = [string]$repo.full_name
        if (-not $fullName) { continue }

        if ($fullName.ToLowerInvariant() -eq $anchor.FullName.ToLowerInvariant()) { continue }
        if (-not $AllowSameOwner -and ([string]$repo.owner.login).ToLowerInvariant() -eq $anchor.Owner.ToLowerInvariant()) { continue }
        if (-not $AllowForks -and [bool]$repo.fork) { continue }
        if (-not $AllowArchived -and [bool]$repo.archived) { continue }
        if ([int]$repo.stargazers_count -lt $MinimumStars) { continue }

        $candidate = [PSCustomObject]@{
            FullName     = [string]$repo.full_name
            Name         = ([string]$repo.full_name -split '/')[1]
            Url          = [string]$repo.html_url
            Description  = [string]$repo.description
            Topics       = @()  # fetched later
            Language     = [string]$repo.language
            Stars        = [int]$repo.stargazers_count
            Fork         = [bool]$repo.fork
            Archived     = [bool]$repo.archived
            CreatedAt    = [datetime]$repo.created_at
            UpdatedAt    = [datetime]$repo.updated_at
            Owner        = [string]$repo.owner.login
            SourceQueries= @($query)
        }

        if ($candidateMap.ContainsKey($candidate.FullName)) {
            $existing = $candidateMap[$candidate.FullName]
            $existing.SourceQueries = @($existing.SourceQueries + $query | Select-Object -Unique)
            $candidateMap[$candidate.FullName] = $existing
        } else {
            $candidateMap[$candidate.FullName] = $candidate
        }
    }
}

$candidates = @($candidateMap.Values)

# Enrich with full repo details for topics and exact repo metadata
$enriched = [System.Collections.Generic.List[object]]::new()
foreach ($cand in $candidates) {
    try {
        $d = Get-RepoDetails -FullName $cand.FullName
        $cand.Topics = @($d.Topics)
        $cand.Language = if ($d.Language) { $d.Language } else { $cand.Language }
        $cand.Stars = if ($d.Stars -gt 0) { $d.Stars } else { $cand.Stars }
        $cand.CreatedAt = $d.CreatedAt
        $cand.UpdatedAt = $d.UpdatedAt
        $cand.Fork = $d.Fork
        $cand.Archived = $d.Archived
        $cand.Description = if ($d.Description) { $d.Description } else { $cand.Description }
    } catch {
        # keep partial candidate if detail enrichment fails
    }

    if (Test-JunkRepo -Repo $cand) { continue }
    $enriched.Add($cand) | Out-Null
}

$scored = foreach ($cand in $enriched) {
    $parts = Score-Candidate -Anchor $anchorObj -Candidate $cand -MatchedQueries @($cand.SourceQueries) -CrossAnchorFreq $freqMap

    $why = @()
    if ($parts.Score -ge $MinimumScore) { $why += "Score>=MinimumScore" } else { $why += "Score<MinimumScore" }
    if (-not $AllowSameOwner -and $cand.Owner.ToLowerInvariant() -eq $anchorObj.Owner.ToLowerInvariant()) { $why += "SameOwnerBlocked" }
    if (-not $AllowForks -and $cand.Fork) { $why += "ForkBlocked" }
    if (-not $AllowArchived -and $cand.Archived) { $why += "ArchivedBlocked" }
    if ($cand.Stars -lt $MinimumStars) { $why += "BelowMinStars" }

    [PSCustomObject]@{
        AnchorRepo              = $anchorObj.FullName
        AnchorUrl               = $anchorObj.Url
        CandidateRepo           = $cand.FullName
        CandidateUrl            = $cand.Url
        CandidateOwner          = $cand.Owner
        CandidateLanguage       = $cand.Language
        CandidateStars          = $cand.Stars
        CandidateSubdomain      = $parts.CandidateSubdomain
        Rank                    = 0

        # Scoring outputs
        Score                   = $parts.Score
        ScoreBase               = $parts.ScoreBase
        PenaltyCrossAnchorFreq  = $parts.PenaltyCrossAnchorFreq
        PenaltyRetrieval        = (if ($IncludeRetrievalSignalsInScore) { 0.0 } else { [math]::Round($ScoreWeights.QueryCoverage * $parts.QueryCoverage, 2) })
        PenaltyNotes            = (if ($IncludeRetrievalSignalsInScore) { "" } else { "QueryCoverage excluded from Score (recommended)." })

        Qualified               = ($parts.Score -ge $MinimumScore)

        # Feature diagnostics
        TopicJaccard            = $parts.TopicJaccard
        LexicalJaccard          = $parts.LexicalJaccard
        LanguageMatch           = $parts.LanguageMatch
        StarSimilarity          = $parts.StarSimilarity
        RecencySimilarity       = $parts.RecencySimilarity
        SubdomainMatch          = $parts.SubdomainMatch
        QueryCoverage           = $parts.QueryCoverage

        # Explainability
        TopSignals              = $parts.TopSignals
        ScoreBreakdownJson      = $parts.ScoreBreakdownJson
        WhyQualified            = ($why -join ";")

        # Provenance
        SourceQueries           = (@($cand.SourceQueries | Select-Object -Unique) -join " | ")
        Description             = $cand.Description
    }
}

$scored = @($scored | Sort-Object -Property @{Expression='Score';Descending=$true}, @{Expression='CandidateStars';Descending=$true}, @{Expression='CandidateRepo';Descending=$false})
$qualified = @($scored | Where-Object { $_.Qualified })

# Diversity guard selection
$diversityEnabled = (-not $DisableDiversityGuard) -and ($MaxPerOwner -gt 0 -or $MaxPerOwnerPerSubdomain -gt 0)

function Select-WithCaps {
    param(
        [Parameter(Mandatory=$true)][object[]]$Items,
        [Parameter(Mandatory=$true)][int]$TopK,
        [int]$MaxPerOwner,
        [int]$MaxPerOwnerPerSubdomain
    )

    $countsOwner = @{}
    $countsOwnerSub = @{}
    $picked = [System.Collections.Generic.List[object]]::new()

    foreach ($it in $Items) {
        if (@($picked).Count -ge $TopK) { break }

        $owner = [string]$it.CandidateOwner
        $sub = [string]$it.CandidateSubdomain
        if (-not $sub) { $sub = "__none__" }
        $key = "$owner|$sub"

        if ($MaxPerOwner -gt 0) {
            if (-not $countsOwner.ContainsKey($owner)) { $countsOwner[$owner] = 0 }
            if ($countsOwner[$owner] -ge $MaxPerOwner) { continue }
        }

        if ($MaxPerOwnerPerSubdomain -gt 0) {
            if (-not $countsOwnerSub.ContainsKey($key)) { $countsOwnerSub[$key] = 0 }
            if ($countsOwnerSub[$key] -ge $MaxPerOwnerPerSubdomain) { continue }
        }

        if ($MaxPerOwner -gt 0) { $countsOwner[$owner]++ }
        if ($MaxPerOwnerPerSubdomain -gt 0) { $countsOwnerSub[$key]++ }

        $picked.Add($it) | Out-Null
    }

    return ,@($picked)
}

$final = [System.Collections.Generic.List[object]]::new()

if ($diversityEnabled) {
    $seed = Select-WithCaps -Items $qualified -TopK $TopK -MaxPerOwner $MaxPerOwner -MaxPerOwnerPerSubdomain $MaxPerOwnerPerSubdomain
    foreach ($item in $seed) { $final.Add($item) | Out-Null }

    if (@($final).Count -lt $TopK) {
        $needed = $TopK - @($final).Count
        $existingRepos = @($final | ForEach-Object { $_.CandidateRepo })
        $fill = @($qualified | Where-Object { ($existingRepos -notcontains $_.CandidateRepo) } | Select-Object -First $needed)
        foreach ($item in $fill) { $final.Add($item) | Out-Null }
    }
} else {
    foreach ($item in ($qualified | Select-Object -First $TopK)) { $final.Add($item) | Out-Null }
}

if ($AllowFallbackFill -and @($final).Count -lt $TopK) {
    $needed = $TopK - @($final).Count
    $existingRepos = @($final | ForEach-Object { $_.CandidateRepo })
    $fallback = @($scored | Where-Object { ($existingRepos -notcontains $_.CandidateRepo) } | Select-Object -First $needed)
    foreach ($item in $fallback) { $final.Add($item) | Out-Null }
}

$rank = 1
foreach ($item in $final) { $item.Rank = $rank; $rank++ }

# Output paths
$anchorPath = Join-Path $OutputDir "anchor_repo.json"
$candidatesJsonPath = Join-Path $OutputDir "candidate_repos.json"
$candidatesCsvPath = Join-Path $OutputDir "candidate_repos.csv"
$rankedJsonPath = Join-Path $OutputDir "ranked_matches.json"
$rankedCsvPath = Join-Path $OutputDir "ranked_matches.csv"
$finalCsvPath = Join-Path $OutputDir "30_Matches.csv"
$manifestPath = Join-Path $OutputDir "run_manifest.json"

# Write artifacts
$anchorObj | ConvertTo-Json -Depth 8 | Set-Content -Path $anchorPath -Encoding UTF8
$enriched | ConvertTo-Json -Depth 8 | Set-Content -Path $candidatesJsonPath -Encoding UTF8
$enriched | Select-Object FullName,Url,Owner,Language,Stars,Fork,Archived,CreatedAt,UpdatedAt,Description,@{N='Topics';E={($_.Topics -join ';')}},@{N='SourceQueries';E={($_.SourceQueries -join ' | ')}} |
    Export-Csv -Path $candidatesCsvPath -NoTypeInformation -Encoding UTF8
$scored | ConvertTo-Json -Depth 8 | Set-Content -Path $rankedJsonPath -Encoding UTF8
$scored | Export-Csv -Path $rankedCsvPath -NoTypeInformation -Encoding UTF8
$final | Export-Csv -Path $finalCsvPath -NoTypeInformation -Encoding UTF8

# Run manifest (MetaMatch 2.0): makes runs auditable and reproducible
$gitCommit = ""
try {
    $gitCommit = (& git rev-parse HEAD 2>$null)
    if ($LASTEXITCODE -ne 0) { $gitCommit = "" }
} catch { $gitCommit = "" }

$manifest = [ordered]@{
    tool = "MetaMatch 2.0 (Get-AnchorMatches.ps1)"
    utc_timestamp = (Get-Date).ToUniversalTime().ToString("o")
    git_commit = ($gitCommit.Trim())
    anchor = [ordered]@{
        full_name = $anchorObj.FullName
        url = $anchorObj.Url
        owner = $anchorObj.Owner
        language = $anchorObj.Language
        stars = $anchorObj.Stars
        topics = @($anchorObj.Topics)
    }
    params = [ordered]@{
        TopK = $TopK
        MaxSearchPerQuery = $MaxSearchPerQuery
        MinimumStars = $MinimumStars
        MinimumScore = $MinimumScore
        IncludeRetrievalSignalsInScore = [bool]$IncludeRetrievalSignalsInScore
        CrossAnchorRunsDir = $CrossAnchorRunsDir
        CrossAnchorFreqPenaltyWeight = $CrossAnchorFreqPenaltyWeight
        MaxPerOwner = $MaxPerOwner
        MaxPerOwnerPerSubdomain = $MaxPerOwnerPerSubdomain
        DisableDiversityGuard = [bool]$DisableDiversityGuard
        AllowSameOwner = [bool]$AllowSameOwner
        AllowForks = [bool]$AllowForks
        AllowArchived = [bool]$AllowArchived
        AllowFallbackFill = [bool]$AllowFallbackFill
    }
    weights = $ScoreWeights
    counts = [ordered]@{
        search_queries = @($searchQueries).Count
        candidate_pool = @($candidates).Count
        enriched = @($enriched).Count
        scored = @($scored).Count
        qualified = @($qualified).Count
        final = @($final).Count
    }
    outputs = [ordered]@{
        anchor_repo_json = $anchorPath
        candidate_repos_csv = $candidatesCsvPath
        ranked_matches_csv = $rankedCsvPath
        final_matches_csv = $finalCsvPath
    }
}
$manifest | ConvertTo-Json -Depth 10 | Set-Content -Path $manifestPath -Encoding UTF8

Write-Host ""
Write-Host "Wrote:" -ForegroundColor Cyan
Write-Host "  - $anchorPath"
Write-Host "  - $candidatesJsonPath"
Write-Host "  - $candidatesCsvPath"
Write-Host "  - $rankedJsonPath"
Write-Host "  - $rankedCsvPath"
Write-Host "  - $finalCsvPath"
Write-Host "  - $manifestPath"
Write-Host ""
Write-Host "Final match count: $(@($final).Count)" -ForegroundColor Green
Write-Host "Qualified above threshold: $(@($qualified).Count)" -ForegroundColor Green
if (@($final).Count -lt $TopK) { Write-Host "WARNING: Only $(@($final).Count) matches were available after filtering." -ForegroundColor Yellow }