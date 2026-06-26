# Downstream validation summary

Quantified proxy triage, candidate search effort, and testing-relevance coverage
for three queryv2 anchors using frozen MetaMatch + REDUX outputs.

## Proxy triage efficiency

| Anchor | Qualified pool | REDUX pass @50 (top-5) | Reduction vs pool |
|--------|----------------|------------------------|-----------------|
| apache-airflow | 9 | 5 | 44.44% |
| ray-project-ray | 6 | 5 | 16.67% |
| huggingface-transformers | 18 | 5 | 72.22% |

## Candidate search effort

Median repos a reviewer inspects to reach high-similarity proxy (REDUX metadata ≥ 50):

- **apache-airflow**: unfiltered qualified=9, MetaMatch top-5=5, REDUX-filtered=5
- **ray-project-ray**: unfiltered qualified=6, MetaMatch top-5=5, REDUX-filtered=5
- **huggingface-transformers**: unfiltered qualified=18, MetaMatch top-5=5, REDUX-filtered=5

## Testing relevance (scenario coverage)

Top-3 REDUX proxies mapped to CAIS test-scenario dimensions vs bottom-ranked baseline.
See `scenario_coverage.csv` and `testing_case_study_airflow.md` for narrative.

## Gate G9 (informational)

Downstream usefulness is supportive evidence; it does not replace G1–G8 retrieval hygiene gates.

