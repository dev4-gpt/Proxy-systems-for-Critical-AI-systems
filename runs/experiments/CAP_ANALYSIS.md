# Do owner caps matter? (from archived experiments)

Compared runs that **only differ** in `MaxPerOwner` / `MaxPerOwnerPerSubdomain` at **penalty=110, min=700**:

| experiment_id | cap | Top5 mag | Weak | Good | OK | Lightning f30 | Keras | Streamlit |
|---------------|-----|----------|------|------|-----|---------------|-------|-----------|
| cap11 (1/1) | 1/1 | 17 | 2 | 15 | 3 | 11 | 12 | 9 |
| cap12 (1/2) | 1/2 | 17 | 2 | 15 | 3 | 11 | 12 | 9 |
| cap21 (2/1) | 2/1 | 17 | 2 | 15 | 3 | 11 | 12 | 9 |
| cap22 (2/2) | 2/2 | 17 | 2 | 15 | 3 | 11 | 12 | 8 |

**Conclusion:** For this penalty/min, caps did **not** change Good/OK/Weak or Top5 magnet totals. Only a small Streamlit final-30 difference (9 vs 8).

At **penalty=150, min=700**, only **cap22** was run (winner on Top5 magnets vs penalty100).

**Recommendation for new runs:** use **cap 2/2** (consistent with current winner). No extra cap-only run unless a new (penalty, min) pair looks cap-sensitive.

Untested cap at min700 we have **not** tried at high penalty: **cap11 (1/1)** at penalty 175 — only add if batch-3 results are flat and you want one more probe.
