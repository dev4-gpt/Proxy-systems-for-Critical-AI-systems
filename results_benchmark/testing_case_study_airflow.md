# Testing-outcome case study: `apache/airflow` (queryv2)

Links MetaMatch retrieval (queryv2 winner) to REDUX similarity and CAIS test-scenario dimensions.

## Anchor and retrieval (MetaMatch)

- **Anchor:** `apache/airflow` — workflow orchestration CAIS stand-in candidate.
- **queryv2 metrics:** Good tier; 0 magnets in top 5; final-30 unique pool ≈ 9 (thin).
- **Top-3 proxies** (from `penalty300_min700_cap22_queryv2/manual-ml-py/apache-airflow/30_Matches.csv`):


| Rank | Proxy                              | Role                        |
| ---- | ---------------------------------- | --------------------------- |
| 1    | feast-dev/feast                    | Feature store / ML data ops |
| 2    | dagster-io/dagster                 | Data orchestration          |
| 3    | abhishek-ch/around-dataengineering | Data-engineering patterns   |


## REDUX similarity (stand-in adequacy)

From `queryv2_redux/apache-airflow.csv` (full-cohort metadata REDUX, top-5):


| Proxy                              | Metadata % |
| ---------------------------------- | ---------- |
| feast-dev/feast                    | 96.4       |
| dagster-io/dagster                 | 96.3       |
| abhishek-ch/around-dataengineering | 93.6       |


**Interpretation:** Top orchestration-adjacent proxies score **>93% metadata similarity** to `apache/airflow`, supporting stand-in adequacy on commit-metadata fingerprints. Rank #3 still trails feast/dagster slightly; pair with scenario rubric checks before claiming full test coverage.

## CAIS test-scenario mapping (NIST-style loop)

Per README / `CAIS_TEST_SCENARIOS` in REDUX notebook, we map proxies to **orchestration / integration** dimensions:


| Proxy                              | Scenario dimension                | Example test focus                                        |
| ---------------------------------- | --------------------------------- | --------------------------------------------------------- |
| feast-dev/feast                    | Data pipeline reliability         | Offline/online feature consistency under workflow changes |
| dagster-io/dagster                 | Orchestration & dependency graphs | DAG failure propagation, retry semantics                  |
| abhishek-ch/around-dataengineering | ETL / integration hygiene         | Connector failure handling, idempotent tasks              |


**Narrative:** High-similarity proxies support **workflow and data-pipeline** test campaigns; they do not replace domain-specific safety cases (like export-controlled CAIS logic) without additional rubric checks.

## Separation from retrieval metrics

- Magnets / Good-OK-Weak prove **GitHub search hygiene** only.
- This case study is the minimum bridge from similarity -> **test-relevant** outcomes

