# Full Projected Pair Run

- Pairs generated: 25
- Target uncertain selected: 5
- Target uncertain required: 5
- API requests: 54
- API latency p95 (ms): 1772.9
- Total retries: 15
- Authenticated: yes
- Go/No-Go: GO

## Decision Gates
- agreement_pearson: pass
- agreement_spearman: pass
- equivalence_or_directionality: pass
- uncertain_pair_coverage: pass
- api_health: pass

## Timing by stage
- control_rows: 0.0 ms
- discover_uncertain_pairs: 75617.6 ms
- stats: 17.9 ms
- step_load_benchmark: 7868.9 ms

## Step-load benchmark
- workers=1: throughput=0.78 req/s, p95=1452.2ms
- workers=2: throughput=1.49 req/s, p95=1819.7ms
