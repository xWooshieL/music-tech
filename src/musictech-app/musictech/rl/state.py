"""State encoding for the tempo prediction RL agent.

The thesis (Fig. 1, eq. 1) defines the agent state as

    s_t = (α̂_t, τ_{t-K:t}, e_{t-K:t}, φ̂(t) / N)

where
    α̂_t                       — compressed posterior of the follower over
                                  score positions (``AlphaSummary``);
    τ_{t-K:t}                  — last K tempo estimates;
    e_{t-K:t}                  — last K emission errors;
    φ̂(t) / N                  — normalized current score position.

This module provides:

1. A compression of the full forward distribution ``α_t`` into
   ``AlphaSummary`` (used both at training and inference time).
2. A ``HistoryBuffer`` class for rolling K-element windows that survives
   resets and never allocates inside the realtime hot path.
3. ``encode_state(...)`` that assembles the four parts into the typed
   ``RLObservation`` DTO declared in ``musictech.core.dto``.

The code is pure numpy. No torch, no gymnasium, no pygame.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from musictech.core.dto import AlphaSummary, FollowerOutput, RLObservation


# ---------------------------------------------------------------------------
# Posterior compression
# ---------------------------------------------------------------------------


def summarize_alpha(alpha: np.ndarray, current_index: int) -> AlphaSummary:
    """Compress the N-dimensional forward distribution into seven scalars.

    Parameters
    ----------
    alpha
        Normalized forward variable ``α_t``; ``alpha.sum() ≈ 1``.
        Expected shape: ``(N,)`` where N is the number of score states.
    current_index
        Most likely score state at the previous step. Used to compute the
        ``top3_indices`` relative to the current position, which keeps the
        feature comparable across pieces of different length.

    Returns
    -------
    AlphaSummary
        A frozen dataclass with ``max_value``, ``entropy``,
        ``argmax_normalized``, ``top3_indices`` and ``top3_mass``.

    Notes
    -----
    Entropy is computed in nats (natural log). For empty or all-zero ``α``
    we return a degenerate summary rather than raising — this keeps the
    realtime path robust to numerical underflow.
    """
    if alpha.size == 0:
        return AlphaSummary(
            max_value=0.0,
            entropy=0.0,
            argmax_normalized=0.0,
            top3_indices=(0, 0, 0),
            top3_mass=0.0,
        )

    total = float(alpha.sum())
    if total <= 0.0 or not np.isfinite(total):
        return AlphaSummary(
            max_value=0.0,
            entropy=0.0,
            argmax_normalized=float(current_index) / max(alpha.size, 1),
            top3_indices=(current_index, current_index, current_index),
            top3_mass=0.0,
        )

    # Always work on a normalized copy so the caller can pass un-normalized α.
    probs = alpha / total

    max_value = float(probs.max())
    argmax = int(probs.argmax())

    # Entropy in nats; mask zeros to avoid log(0).
    nonzero = probs[probs > 0.0]
    entropy = float(-(nonzero * np.log(nonzero)).sum())

    # Top-3 indices and their summed mass.
    k = min(3, probs.size)
    top_k = np.argpartition(probs, -k)[-k:]
    # Sort the top-k by probability descending so that index [0] is the mode.
    top_k_sorted = top_k[np.argsort(-probs[top_k])]
    top3_mass = float(probs[top_k_sorted].sum())

    # Pad to length 3 if the score is shorter than 3 (degenerate).
    indices = [int(i) for i in top_k_sorted]
    while len(indices) < 3:
        indices.append(indices[-1] if indices else 0)
    top3_indices = (indices[0], indices[1], indices[2])

    return AlphaSummary(
        max_value=max_value,
        entropy=entropy,
        argmax_normalized=float(argmax) / probs.size,
        top3_indices=top3_indices,
        top3_mass=top3_mass,
    )


# ---------------------------------------------------------------------------
# Rolling history buffers
# ---------------------------------------------------------------------------


@dataclass
class HistoryBuffer:
    """Fixed-length FIFO buffer for tempo / emission-error history.

    Backed by a pre-allocated numpy array to keep ``push()`` allocation-free
    in the realtime hot path. The buffer is initialised with the ``fill``
    value so that early steps (before K observations have arrived) still
    yield a fixed-length window suitable for an MLP input.
    """

    capacity: int
    fill: float = 1.0

    def __post_init__(self) -> None:
        if self.capacity <= 0:
            raise ValueError("HistoryBuffer capacity must be positive")
        self._data: np.ndarray = np.full(self.capacity, self.fill, dtype=np.float64)

    def push(self, value: float) -> None:
        """Append a value; oldest entry is dropped."""
        # Shift left and write the new value at the last position. For K<=64
        # this is faster than collections.deque and gives a contiguous view.
        self._data[:-1] = self._data[1:]
        self._data[-1] = float(value)

    def view(self) -> np.ndarray:
        """Return a read-only view over the current contents (length K)."""
        v = self._data.view()
        v.flags.writeable = False
        return v

    def reset(self) -> None:
        """Restore the buffer to its initial fill value."""
        self._data.fill(self.fill)


# ---------------------------------------------------------------------------
# Top-level state encoder
# ---------------------------------------------------------------------------


def encode_state(
    follower_output: FollowerOutput,
    tempo_history: np.ndarray,
    emission_error_history: np.ndarray,
    score_length: int,
) -> RLObservation:
    """Assemble the four components into an ``RLObservation``.

    This is the single entry point that connects the tracker layer
    (``musictech.core``) to the RL layer. Both histories are passed in
    as ready-made numpy windows (see :class:`HistoryBuffer`); the encoder
    itself does not maintain state.

    Parameters
    ----------
    follower_output
        Output of one HSMM / hybrid step. Must already contain a populated
        ``alpha_summary`` field.
    tempo_history
        Length-K array of tempo coefficients τ for the last K ticks.
    emission_error_history
        Length-K array of emission errors e for the last K ticks.
        ``e_t = -log b_{argmax(α_t)}(o_t)``; the encoder does not compute
        the error itself — the tracker is the only place that has access
        to the emission function.
    score_length
        Number of states in the score (``N``). Used to normalize the score
        position to the [0, 1] interval, which keeps the input to the MLP
        comparable across pieces.

    Returns
    -------
    RLObservation
        The thesis ``s_t``, ready to be flattened by
        :meth:`RLObservation.as_vector` and fed to the policy network.
    """
    if score_length <= 0:
        raise ValueError("score_length must be positive")
    if tempo_history.ndim != 1 or emission_error_history.ndim != 1:
        raise ValueError("history buffers must be 1-D arrays")
    if tempo_history.size != emission_error_history.size:
        raise ValueError(
            f"history buffers must have equal length, got "
            f"{tempo_history.size} and {emission_error_history.size}"
        )

    position_normalized = float(follower_output.score_index) / score_length
    # Clamp to [0, 1] in case the follower temporarily over-shoots N
    # (can happen during anchored resyncs).
    position_normalized = min(1.0, max(0.0, position_normalized))

    return RLObservation(
        alpha=follower_output.alpha_summary,
        tempo_history=np.asarray(tempo_history, dtype=np.float64),
        emission_error_history=np.asarray(emission_error_history, dtype=np.float64),
        score_position_normalized=position_normalized,
    )


__all__ = [
    "HistoryBuffer",
    "encode_state",
    "summarize_alpha",
]
