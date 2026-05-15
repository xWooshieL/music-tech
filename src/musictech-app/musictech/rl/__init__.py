"""RL tempo agent — the core research contribution of the thesis.

This sub-package implements the hybrid architecture from
``papers/тезисы.pdf`` Fig. 1: a lightweight RL policy that sits *next* to
the classical probabilistic tracker and predicts the orchestra tempo
coefficient ``a_t ∈ [0.5, 2.0]`` over the next 200–500 ms.

The agent does not replace the follower. It reads
``FollowerOutput.alpha_summary`` and a short history of tempo / emission
error, and outputs a single scalar that the orchestra renderer applies.

Currently implemented (skeleton — no training yet)
--------------------------------------------------

- ``state.py``     ── ``encode_state`` plus ``summarize_alpha`` and
                       ``HistoryBuffer`` for K-element rolling windows.
- ``reward.py``    ── ``compute_reward`` (thesis eq. 1) with separated
                       diagnostic components.
- ``env.py``       ── ``ScoreFollowingEnv`` (gymnasium-compatible, but
                       gymnasium is optional).
- ``policy.py``    ── ``MLPPolicy``: pure-numpy 2×64 MLP with
                       sigmoid-rescale output head; trainable from a
                       notebook, deployable in the realtime path.

Planned (left blank intentionally)
----------------------------------

- ``simulator.py`` — parametric rubato simulator (Repp 1995) for PPO rollouts.
- ``train_bc.py``  — behavior cloning on ASAP-derived oracle tempo.
- ``train_ppo.py`` — PPO fine-tuning with KL penalty to BC (Jaques 2017 [13]).

Constraints
-----------

- Inference path must stay under ~1 ms on CPU (MLP 2×64 is ~50 µs).
- No ``pygame`` / ``mido`` imports — keep the layer test-friendly.
- All DTOs come from :mod:`musictech.core.dto`; do not define new ones here.
"""

from musictech.rl.env import (
    EmissionErrorFn,
    EnvConfig,
    FollowerStepFn,
    PerformerStepFn,
    RendererClockFn,
    ScoreFollowingEnv,
)
from musictech.rl.policy import MLPPolicy, PolicyConfig
from musictech.rl.reward import (
    DEFAULT_LAMBDA,
    DEFAULT_MU,
    SYNC_ERROR_CLIP,
    RewardConfig,
    compute_reward,
)
from musictech.rl.state import HistoryBuffer, encode_state, summarize_alpha

__all__ = [
    "DEFAULT_LAMBDA",
    "DEFAULT_MU",
    "EmissionErrorFn",
    "EnvConfig",
    "FollowerStepFn",
    "HistoryBuffer",
    "MLPPolicy",
    "PerformerStepFn",
    "PolicyConfig",
    "RendererClockFn",
    "RewardConfig",
    "SYNC_ERROR_CLIP",
    "ScoreFollowingEnv",
    "compute_reward",
    "encode_state",
    "summarize_alpha",
]
