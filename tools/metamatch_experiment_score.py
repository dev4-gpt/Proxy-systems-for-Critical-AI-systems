"""Shared ranking helpers for MetaMatch experiment comparison."""

from __future__ import annotations


def int_val(row: dict, key: str, default: int = 0) -> int:
    try:
        return int(float(row.get(key) or default))
    except (TypeError, ValueError):
        return default


def magnet_final30_sum(row: dict) -> int:
    return sum(int_val(row, k) for k in row if k.startswith("MagnetFinal30_"))


def hub_final30(row: dict) -> tuple[int, int, int]:
    return (
        int_val(row, "MagnetFinal30_pytorch-lightning"),
        int_val(row, "MagnetFinal30_keras"),
        int_val(row, "MagnetFinal30_streamlit"),
    )


def score_row(row: dict, max_weak: int = 99) -> tuple:
    """Lower is better. (top5 magnets, final30 magnet sum, weak count, id)."""
    weak = int_val(row, "Weak")
    if weak > max_weak:
        return (9999, 9999, 9999, row.get("experiment_id", ""))
    return (
        int_val(row, "TotalMagnetsInTop5"),
        magnet_final30_sum(row),
        weak,
        row.get("experiment_id", ""),
    )


def row_by_id(rows: list[dict], eid: str) -> dict | None:
    for r in rows:
        if r.get("experiment_id") == eid:
            return r
    return None


def beats_row(candidate: dict, reference: dict, max_weak: int = 99) -> bool:
    return score_row(candidate, max_weak) < score_row(reference, max_weak)
