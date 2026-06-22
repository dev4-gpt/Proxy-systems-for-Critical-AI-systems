# queryv2 spot-check (read-only)

Archive: `runs/experiments/penalty300_min700_cap22_queryv2/manual-ml-py/`

Thin-anchor retrieval pools (final-30 unique count from experiment scorecard):


| Anchor                | Final30 unique | Top-5 proxies (Rank 1–5)                                                                                                                                  | Notes                                          |
| --------------------- | -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| jina-ai/serve         | 3              | bentoml/BentoML, Netflix/metaflow, hongbo-miao/hongbomiao.com, DaoCloud/DaoCloud-docs, PrefectHQ/fastmcp                                                  | Small pool; top picks are serving/LLM adjacent |
| ray-project/ray       | 6              | torchpipe/torchpipe, ELS-RD/transformer-deploy, curiousily/Deploy-BERT-for-Sentiment-Analysis-with-FastAPI, run-llama/llama_deploy, NVIDIA/TensorRT-LLM | Thin; verify distributed-ML adjacency          |
| apache/airflow        | 9              | feast-dev/feast, dagster-io/dagster, abhishek-ch/around-dataengineering, san089/goodreads_etl_pipeline, elyra-ai/elyra                                    | Workflow/orchestration neighbors               |
| OpenBB-finance/OpenBB | 11             | ValueCell-ai/valuecell, brokermr810/QuantDinger, quantsbin/Quantsbin, Michalos88/Quant-Projects, binance/binance-skills-hub                               | Quant/finance tooling neighbors                |


## Retrieval hygiene (queryv2 winner)

- Top-5 magnet hits: **0**
- Good / OK / Weak: **20 / 0 / 0**
- Lightning / Keras / Streamlit in final 30: **2 / 2 / 1**

Magnets/Good-OK-Weak measure **GitHub retrieval hygiene**, not REDUX similarity or test-scenario coverage.

## Next validation

REDUX scores for anchor -> proxy pairs are written under `results_benchmark/queryv2_redux/` by `tools/score_metamatch_proxies_redux.py`.