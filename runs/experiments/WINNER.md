# MetaMatch experiment winner

**Champion (prior best):** `penalty100_min700_cap21`
- TotalMagnetsInTop5=18, Weak=2, final30 magnet sum=59

**Best in comparison table:** `penalty200_min700_cap22`
**Beats champion:** yes

## Full scorecard (lower is better)

| experiment_id | penalty | min | cap | Top5 mag | Weak | Good | OK | L/K/S f30 | f30 sum |
|---------------|---------|-----|-----|----------|------|------|-----|-----------|---------|
| penalty200_min700_cap22 ** | 200.0 | 700 | 2/2 | 10 | 1 | 17 | 2 | 8/9/7 | 37 |
| penalty200_min600_cap22 | 200.0 | 600 | 2/2 | 10 | 1 | 17 | 2 | 8/9/8 | 38 |
| penalty175_min600_cap22 | 175.0 | 600 | 2/2 | 11 | 1 | 17 | 2 | 10/10/8 | 44 |
| penalty175_min700_cap22 | 175.0 | 700 | 2/2 | 11 | 1 | 17 | 2 | 10/10/8 | 44 |
| penalty150_min600_cap22 | 150.0 | 600 | 2/2 | 12 | 2 | 17 | 1 | 11/12/8 | 51 |
| penalty150_min700_cap22 | 150.0 | 700 | 2/2 | 12 | 2 | 17 | 1 | 11/12/8 | 51 |
| penalty110_min700_cap22 | 110.0 | 700 | 2/2 | 17 | 2 | 15 | 3 | 11/12/8 | 56 |
| penalty110_min700_cap11 | 110.0 | 700 | 1/1 | 17 | 2 | 15 | 3 | 11/12/9 | 57 |
| penalty110_min700_cap12 | 110.0 | 700 | 1/2 | 17 | 2 | 15 | 3 | 11/12/9 | 57 |
| penalty110_min700_cap21 | 110.0 | 700 | 2/1 | 17 | 2 | 15 | 3 | 11/12/9 | 57 |
| penalty100_min700_cap21 | 100.0 | 700 | 2/1 | 18 | 2 | 14 | 4 | 11/12/10 | 59 |
| penalty75_min700_cap21 | 75.0 | 700 | 2/1 | 19 | 2 | 12 | 6 | 10/10/11 | 53 |
| penalty30_min700_cap21 | 30.0 | 700 | 2/1 | 30 | 8 | 10 | 2 | 12/12/12 | 67 |
| penalty55_min700_cap11 | 55.0 | 700 | 1/1 | 26 | 5 | 11 | 4 | 12/12/12 | 65 |
| penalty55_min700_cap21 | 55.0 | 700 | 2/1 | 26 | 5 | 11 | 4 | 12/12/12 | 65 |
| penalty55_min700_cap21_nofallback | 55.0 | 700 | 2/1 | 26 | 5 | 11 | 4 | 11/12/11 | 63 |
| penalty55_min750_cap21 | 55.0 | 750 | 2/1 | 26 | 5 | 11 | 4 | 12/12/12 | 65 |

## Recommended defaults for Get-AnchorMatches.ps1

Use: **`penalty200_min700_cap22`** (new grid winner)

- CrossAnchorFreqPenaltyWeight: 200.0
- MinimumScore: 700
- MaxPerOwner: 2
- MaxPerOwnerPerSubdomain: 2
- AllowFallbackFill: true
