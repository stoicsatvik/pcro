"""Optional neural replay-success surrogate.

Neural training is intentionally optional. A large model is not useful until the experiment store
contains enough real replay outcomes. This module provides the hook once that data exists.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence


def train_replay_mlp(
    rows: Iterable[tuple[Sequence[float], int]],
    *,
    epochs: int = 100,
    hidden: int = 32,
    learning_rate: float = 1e-3,
):
    try:
        import torch
        from torch import nn
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("PyTorch is required for the optional neural surrogate") from exc

    materialized = [(list(features), int(label)) for features, label in rows]
    if not materialized:
        raise ValueError("training rows cannot be empty")
    input_dim = len(materialized[0][0])
    if input_dim <= 0 or any(len(features) != input_dim for features, _ in materialized):
        raise ValueError("all rows must share a non-zero feature dimension")

    model = nn.Sequential(
        nn.Linear(input_dim, hidden),
        nn.ReLU(),
        nn.Linear(hidden, hidden),
        nn.ReLU(),
        nn.Linear(hidden, 1),
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)
    loss_fn = nn.BCEWithLogitsLoss()
    x = torch.tensor([features for features, _ in materialized], dtype=torch.float32)
    y = torch.tensor([[label] for _, label in materialized], dtype=torch.float32)

    model.train()
    for _ in range(max(1, epochs)):
        optimizer.zero_grad(set_to_none=True)
        logits = model(x)
        loss = loss_fn(logits, y)
        loss.backward()
        optimizer.step()
    return model
