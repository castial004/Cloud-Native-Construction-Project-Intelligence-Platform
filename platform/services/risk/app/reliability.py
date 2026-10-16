"""Probabilistic schedule-reliability formulation (IEEE paper Sec. V-B, Eq. 8).

Implements a differentiable Softmax surrogate of the CPM max operator to locate
the Most Probable Point (MPP) of schedule failure across an activity network.

For an activity j, early-finish E_j = S_j + D_j (start + duration). The classic
CPM forward pass uses a non-differentiable max over predecessors; we replace it
with a temperature-scaled softmax so gradients can be backpropagated to find the
path most likely to drive a schedule overrun.
"""
from __future__ import annotations

import numpy as np


def softmax(x: np.ndarray, temperature: float = 1.0) -> np.ndarray:
    """Numerically-stable temperature-scaled softmax."""
    x = np.asarray(x, dtype=float)
    if x.size == 0:
        return x
    z = x / max(temperature, 1e-9)
    z = z - np.max(z)
    e = np.exp(z)
    return e / np.sum(e)


def softmax_early_finish(
    predecessor_early_finishes: np.ndarray,
    duration: float,
    temperature: float = 1.0,
) -> float:
    """Differentiable surrogate for max(predecessor finishes) + duration.

    Returns the softmax-weighted expected start plus this activity's duration.
    """
    if predecessor_early_finishes.size == 0:
        return float(duration)
    w = softmax(predecessor_early_finishes, temperature)
    expected_start = float(np.sum(w * predecessor_early_finishes))
    return expected_start + float(duration)


def most_probable_failure_point(
    adjacency: dict[str, list[str]],
    durations: dict[str, float],
    start_id: str,
) -> dict[str, float]:
    """Forward pass computing differentiable early-finish per node.

    adjacency: node -> list of successor ids
    durations: node -> duration (days)
    Returns {node_id: early_finish_days}.
    """
    # Topological order via DFS.
    order: list[str] = []
    visited: set[str] = set()

    def dfs(node: str) -> None:
        if node in visited:
            return
        visited.add(node)
        for succ in adjacency.get(node, []):
            dfs(succ)
        order.append(node)

    dfs(start_id)
    order.reverse()

    predecessors: dict[str, list[str]] = {n: [] for n in order}
    for n, succs in adjacency.items():
        for s in succs:
            predecessors.setdefault(s, []).append(n)

    early_finish: dict[str, float] = {}
    for node in order:
        preds = predecessors.get(node, [])
        pred_ef = np.array([early_finish[p] for p in preds], dtype=float)
        early_finish[node] = softmax_early_finish(pred_ef, durations.get(node, 0.0), temperature=5.0)
    return early_finish
