"""Tempo-prediction policy: a tiny MLP, pure numpy.

The thesis specifies a 2-layer MLP with 64 hidden units and a scalar
output bounded to ``[a_min, a_max]``. At inference time the model needs
sub-millisecond latency on CPU, so we implement it in plain numpy. No
PyTorch dependency in the realtime path.

This module deliberately does *not* implement training. The plan is to
populate the weights either:

1. From a behavior-cloning run done in a Jupyter notebook (PyTorch /
   scikit-learn there is fine — the realtime path will load only the
   final numpy arrays via :meth:`MLPPolicy.load_weights`).
2. From a Stable-Baselines3 PPO checkpoint via a one-time conversion
   script.

Both routes feed the same ``.npz`` artifact, defined in :meth:`save_weights`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from musictech.core.dto import RLAction, RLObservation


# ---------------------------------------------------------------------------
# Activation helpers
# ---------------------------------------------------------------------------


def _tanh(x: np.ndarray) -> np.ndarray:
    """Numerically-stable tanh; relies on numpy's vectorized implementation."""
    return np.tanh(x)


def _sigmoid(x: np.ndarray) -> np.ndarray:
    # Avoid overflow in exp by clipping the input.
    return 1.0 / (1.0 + np.exp(-np.clip(x, -60.0, 60.0)))


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass
class PolicyConfig:
    """Hyperparameters of the policy network.

    Defaults follow the thesis (2×64 MLP). ``input_dim`` is computed from
    the env config (``8 + 2·K``) and must match :class:`RLObservation`
    layout, so we let the caller pass it in rather than guessing.
    """

    input_dim: int
    hidden_dim: int = 64
    n_hidden_layers: int = 2
    action_low: float = 0.5
    action_high: float = 2.0


# ---------------------------------------------------------------------------
# Policy
# ---------------------------------------------------------------------------


@dataclass
class MLPPolicy:
    """Tempo-prediction policy: K-history MLP returning ``a_t``.

    Architecture::

        input  (D=input_dim) ──► [Linear D → H]  ─tanh─►
                                 [Linear H → H]  ─tanh─►   (n_hidden_layers blocks)
                                 [Linear H → 1]  ─sigmoid─►   y ∈ (0, 1)
                                                       │
                       output a_t = low + (high - low) · y   ∈ [low, high]

    A small ``sigmoid``-then-rescale tail keeps the output in the legal
    range without explicit clipping during PPO updates; the value cannot
    saturate exactly at the bounds, which gives PPO well-defined gradients.
    """

    config: PolicyConfig
    weights: list[np.ndarray] = field(default_factory=list)
    biases: list[np.ndarray] = field(default_factory=list)

    @classmethod
    def random_init(cls, config: PolicyConfig, seed: int | None = None) -> "MLPPolicy":
        """Build a policy with He-initialized weights and zero biases.

        Used for unit tests and behavior-cloning warm starts.
        """
        rng = np.random.default_rng(seed)
        weights: list[np.ndarray] = []
        biases: list[np.ndarray] = []

        dims = (
            [config.input_dim]
            + [config.hidden_dim] * config.n_hidden_layers
            + [1]
        )
        for d_in, d_out in zip(dims[:-1], dims[1:]):
            scale = np.sqrt(2.0 / d_in)
            weights.append(rng.normal(0.0, scale, size=(d_in, d_out)))
            biases.append(np.zeros(d_out, dtype=np.float64))
        return cls(config=config, weights=weights, biases=biases)

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def forward(self, x: np.ndarray) -> float:
        """Run one inference pass, returning the rescaled tempo coefficient.

        Parameters
        ----------
        x
            Flattened observation vector of length ``input_dim``.

        Returns
        -------
        float
            ``a_t`` in ``[action_low, action_high]``.
        """
        if x.ndim != 1 or x.size != self.config.input_dim:
            raise ValueError(
                f"input must be a 1-D vector of length {self.config.input_dim}, "
                f"got shape {x.shape}"
            )

        h: np.ndarray = x
        for layer_idx in range(len(self.weights) - 1):
            h = _tanh(h @ self.weights[layer_idx] + self.biases[layer_idx])
        # Final layer
        y = _sigmoid(h @ self.weights[-1] + self.biases[-1])
        scaled = self.config.action_low + (
            self.config.action_high - self.config.action_low
        ) * float(y.flat[0])
        return scaled

    def predict(self, observation: RLObservation | np.ndarray) -> RLAction:
        """Convenience wrapper accepting either ``RLObservation`` or a vector."""
        if isinstance(observation, RLObservation):
            vec = observation.as_vector()
        else:
            vec = np.asarray(observation, dtype=np.float64)
        a = self.forward(vec)
        return RLAction(tempo_coefficient=a)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save_weights(self, path: Path | str) -> None:
        """Serialize the policy to a single ``.npz`` file.

        Layout::

            arr_0 .. arr_{N-1}   weight matrices in order
            bias_0 .. bias_{N-1} bias vectors in order
            meta                 a 0-D object array with the config dict
        """
        path = Path(path)
        kwargs: dict[str, Any] = {}
        for i, (w, b) in enumerate(zip(self.weights, self.biases)):
            kwargs[f"weight_{i}"] = w
            kwargs[f"bias_{i}"] = b
        kwargs["meta"] = np.asarray(
            {
                "input_dim": self.config.input_dim,
                "hidden_dim": self.config.hidden_dim,
                "n_hidden_layers": self.config.n_hidden_layers,
                "action_low": self.config.action_low,
                "action_high": self.config.action_high,
                "n_layers": len(self.weights),
            },
            dtype=object,
        )
        np.savez_compressed(path, **kwargs)

    @classmethod
    def load_weights(cls, path: Path | str) -> "MLPPolicy":
        """Restore a policy previously saved with :meth:`save_weights`."""
        path = Path(path)
        with np.load(path, allow_pickle=True) as data:
            meta = data["meta"].item()
            config = PolicyConfig(
                input_dim=int(meta["input_dim"]),
                hidden_dim=int(meta["hidden_dim"]),
                n_hidden_layers=int(meta["n_hidden_layers"]),
                action_low=float(meta["action_low"]),
                action_high=float(meta["action_high"]),
            )
            n_layers = int(meta["n_layers"])
            weights = [data[f"weight_{i}"].copy() for i in range(n_layers)]
            biases = [data[f"bias_{i}"].copy() for i in range(n_layers)]
        return cls(config=config, weights=weights, biases=biases)


__all__ = [
    "MLPPolicy",
    "PolicyConfig",
]
