# Spot check: penalty300_min700_cap22

Headline metrics: 20 Good, 5 top-five magnet hits. Several anchors still lean on fallback fill (unqualified rows in `30_Matches.csv`).

| Anchor | Qualified/30 | Magnets top5 | Magnets in 30 | Notes |
|--------|--------------|--------------|---------------|-------|
| explosion/spaCy | 3 | 1 | 8 | Lightning in top5 unqualified; 8 magnets in full list |
| streamlit/streamlit | 9 | 1 | 7 | Gradio in top5; UI cross-pull |
| gradio-app/gradio | 3 | 1 | 4 | Streamlit in top5; thin qualified pool |
| recommenders-team/recommenders | **0** | 1 | 5 | Full list from fallback; Lightning in top5 unqualified |
| onnx/onnx | 3 | 1 | 4 | Lightning in top5 unqualified |
| jina-ai/serve | 4 | 0 | 0 | Thin pool; magnets clean |

Query-tuned rerun: `penalty300_min700_cap22_queryv2`. See `PHASE2_NOTES.md`.
