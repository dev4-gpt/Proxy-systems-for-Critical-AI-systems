# Downstream validation summary

Quantified proxy triage, candidate search effort, and testing-relevance coverage
for **24** anchors (20 queryv2 + 4 anchorsv2-only additions)
using frozen MetaMatch + REDUX outputs.

## Proxy triage efficiency


| Anchor                          | Qualified pool | REDUX pass @50 (top-5) | Reduction vs pool |
| ------------------------------- | -------------- | ---------------------- | ----------------- |
| JaidedAI-EasyOCR                | 47             | 5                      | 89.36%            |
| Lightning-AI-pytorch-lightning  | 24             | 5                      | 79.17%            |
| OpenBB-finance-OpenBB           | 11             | 5                      | 54.55%            |
| apache-airflow                  | 9              | 5                      | 44.44%            |
| bbfamily-abu                    | 11             | 5                      | 54.55%            |
| deepspeedai-DeepSpeed           | 10             | 5                      | 50.0%             |
| eriklindernoren-ML-From-Scratch | 11             | 5                      | 54.55%            |
| explosion-spacy                 | 11             | 5                      | 54.55%            |
| gradio-app-gradio               | 18             | 5                      | 72.22%            |
| huggingface-datasets            | 11             | 5                      | 54.55%            |
| huggingface-transformers        | 18             | 5                      | 72.22%            |
| jina-ai-serve                   | 4              | 5                      | -25.0%            |
| mlflow-mlflow                   | 18             | 5                      | 72.22%            |
| onnx-onnx                       | 36             | 5                      | 86.11%            |
| pytorch-pytorch                 | 28             | 5                      | 82.14%            |
| pytorch-vision                  | 14             | 5                      | 64.29%            |
| ray-project-ray                 | 6              | 5                      | 16.67%            |
| recommenders-team-recommenders  | 27             | 5                      | 81.48%            |
| scikit-learn-scikit-learn       | 27             | 5                      | 81.48%            |
| sebastianruder-NLP-progress     | 19             | 5                      | 73.68%            |
| serengil-deepface               | 11             | 5                      | 54.55%            |
| streamlit-streamlit             | 60             | 5                      | 91.67%            |
| treeverse-dvc                   | 1              | 2                      | -100.0%           |
| ultralytics-yolov5              | 26             | 5                      | 80.77%            |




## Candidate search effort

Repos a reviewer inspects to reach high-similarity proxy (REDUX metadata ≥ 50):

- **JaidedAI-EasyOCR**: unfiltered qualified=47, MetaMatch top-5=5, REDUX-filtered=5
- **Lightning-AI-pytorch-lightning**: unfiltered qualified=24, MetaMatch top-5=5, REDUX-filtered=5
- **OpenBB-finance-OpenBB**: unfiltered qualified=11, MetaMatch top-5=5, REDUX-filtered=5
- **apache-airflow**: unfiltered qualified=9, MetaMatch top-5=5, REDUX-filtered=5
- **bbfamily-abu**: unfiltered qualified=11, MetaMatch top-5=5, REDUX-filtered=5
- **deepspeedai-DeepSpeed**: unfiltered qualified=10, MetaMatch top-5=5, REDUX-filtered=5
- **eriklindernoren-ML-From-Scratch**: unfiltered qualified=11, MetaMatch top-5=5, REDUX-filtered=5
- **explosion-spacy**: unfiltered qualified=11, MetaMatch top-5=5, REDUX-filtered=5
- **gradio-app-gradio**: unfiltered qualified=18, MetaMatch top-5=5, REDUX-filtered=5
- **huggingface-datasets**: unfiltered qualified=11, MetaMatch top-5=5, REDUX-filtered=5
- **huggingface-transformers**: unfiltered qualified=18, MetaMatch top-5=5, REDUX-filtered=5
- **jina-ai-serve**: unfiltered qualified=4, MetaMatch top-5=5, REDUX-filtered=5
- **mlflow-mlflow**: unfiltered qualified=18, MetaMatch top-5=5, REDUX-filtered=5
- **onnx-onnx**: unfiltered qualified=36, MetaMatch top-5=5, REDUX-filtered=5
- **pytorch-pytorch**: unfiltered qualified=28, MetaMatch top-5=5, REDUX-filtered=5
- **pytorch-vision**: unfiltered qualified=14, MetaMatch top-5=5, REDUX-filtered=5
- **ray-project-ray**: unfiltered qualified=6, MetaMatch top-5=5, REDUX-filtered=5
- **recommenders-team-recommenders**: unfiltered qualified=27, MetaMatch top-5=5, REDUX-filtered=5
- **scikit-learn-scikit-learn**: unfiltered qualified=27, MetaMatch top-5=5, REDUX-filtered=5
- **sebastianruder-NLP-progress**: unfiltered qualified=19, MetaMatch top-5=5, REDUX-filtered=5
- **serengil-deepface**: unfiltered qualified=11, MetaMatch top-5=5, REDUX-filtered=5
- **streamlit-streamlit**: unfiltered qualified=60, MetaMatch top-5=5, REDUX-filtered=5
- **treeverse-dvc**: unfiltered qualified=1, MetaMatch top-5=2, REDUX-filtered=2
- **ultralytics-yolov5**: unfiltered qualified=26, MetaMatch top-5=5, REDUX-filtered=5



## Testing relevance (scenario coverage)

- **CAIS explicit rubric:** 3 anchors (`apache-airflow`, `ray-project-ray`, `huggingface-transformers`).
- **Metadata heuristic:** 21 anchors — top-3/bottom-2 of REDUX top-5 scored at ≥50 threshold;
no hand-authored CAIS scenario map (see `scenario_coverage.csv` `mapping_mode` column).

Narrative case study: `testing_case_study_airflow.md`.

## Gate G9 (informational)

Downstream usefulness is supportive evidence; it does not replace G1–G8 retrieval hygiene gates.