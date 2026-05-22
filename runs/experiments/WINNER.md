# MetaMatch sweep winner

**Recommended experiment:** `penalty100_min700_cap21`

## Scorecard (lower is better)

| experiment_id | TotalMagnetsInTop5 | Weak | Good | OK | Lightning final30 | Keras | Streamlit |
|---------------|-------------------|------|------|-----|-------------------|-------|-----------|
| penalty100_min700_cap21 | 18 | 2 | 14 | 4 | 11 | 12 | 10 |
| penalty75_min700_cap21 | 19 | 2 | 12 | 6 | 10 | 10 | 11 |
| penalty55_min700_cap21_nofallback | 26 | 5 | 11 | 4 | 11 | 12 | 11 |
| penalty55_min700_cap11 | 26 | 5 | 11 | 4 | 12 | 12 | 12 |
| penalty55_min700_cap21 | 26 | 5 | 11 | 4 | 12 | 12 | 12 |
| penalty55_min750_cap21 | 26 | 5 | 11 | 4 | 12 | 12 | 12 |

## Suggested defaults for Get-AnchorMatches.ps1

- CrossAnchorFreqPenaltyWeight: 100.0
- MinimumScore: 700
- MaxPerOwner: 2
- MaxPerOwnerPerSubdomain: 1

