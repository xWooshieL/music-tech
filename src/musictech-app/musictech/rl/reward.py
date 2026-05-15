"""Reward function for the tempo prediction RL agent.

Implements equation (1) from ``papers/тезисы.pdf``::

    r_t = -|t_render_t - t_perf_t|   ← sync error
          - λ · L_align(t)            ← tracker alignment loss
          - μ · (a_t - a_{t-1})²      ← tempo jerk

All three terms are kept separately in the returned :class:`RLReward`
dataclass so the agent's diagnostics (and PPO advantage debugging) can
plot them independently. The sign convention is: more negative = worse.
"""

from __future__ import annotations

from dataclasses import dataclass

from musictech.core.dto import RLAction, RLReward


# ---------------------------------------------------------------------------
# Default coefficients (Sec. 3 of the thesis)
# ---------------------------------------------------------------------------

DEFAULT_LAMBDA: float = 1.0   # weight on alignment-loss term
DEFAULT_MU: float = 0.5       # weight on tempo-jerk term

# Maximum sane absolute value for any reward component, in seconds. Used to
# clip pathological one-step errors during early training (otherwise a
# single timing spike of 50 s can dominate the PPO advantage estimator).
SYNC_ERROR_CLIP: float = 2.0


@dataclass(frozen=True)
class RewardConfig:
    """Tunable knobs for :func:`compute_reward`.

    Defaults follow the thesis. Treat ``lambda_`` and ``mu`` as
    hyperparameters to be swept during PPO experiments.
    """

    lambda_: float = DEFAULT_LAMBDA
    mu: float = DEFAULT_MU
    sync_error_clip: float = SYNC_ERROR_CLIP


def compute_reward(
    action: RLAction,
    previous_action: RLAction | None,
    t_render: float,
    t_perf: float,
    alignment_loss: float,
    config: RewardConfig | None = None,
) -> RLReward:
    """Evaluate ``r_t`` for one step.

    Parameters
    ----------
    action
        Tempo coefficient ``a_t`` predicted by the policy.
    previous_action
        Tempo coefficient from the previous step ``a_{t-1}``. May be
        ``None`` at the very first step of an episode, in which case the
        tempo-jerk term evaluates to zero (no previous action to compare
        against).
    t_render
        Wall-clock time at which the orchestra renderer emitted the
        soloist's expected note, in seconds.
    t_perf
        Wall-clock time at which the soloist actually played the matched
        note, in seconds.
    alignment_loss
        Non-negative ``L_align(t)`` from the underlying tracker (for
        example, the negative log-likelihood of the observation under the
        forward distribution, or the absolute score-index error against a
        ground-truth alignment when one is available).
    config
        Hyperparameters; defaults to :class:`RewardConfig` with the
        thesis values.

    Returns
    -------
    RLReward
        Dataclass with the total reward and the three components separately,
        for diagnostic purposes.

    Notes
    -----
    The function is pure: no I/O, no global state, no random numbers.
    """
    cfg = config or RewardConfig()
    if cfg.lambda_ < 0 or cfg.mu < 0:
        raise ValueError("lambda and mu must be non-negative")
    if alignment_loss < 0:
        raise ValueError("alignment_loss must be non-negative")

    raw_sync = abs(float(t_render) - float(t_perf))
    sync = min(raw_sync, cfg.sync_error_clip)
    sync_error = -sync

    align_error = -cfg.lambda_ * float(alignment_loss)

    if previous_action is None:
        tempo_jerk = 0.0
    else:
        delta = float(action.tempo_coefficient) - float(previous_action.tempo_coefficient)
        tempo_jerk = -cfg.mu * (delta * delta)

    total = sync_error + align_error + tempo_jerk

    return RLReward(
        total=total,
        sync_error=sync_error,
        alignment_error=align_error,
        tempo_jerk=tempo_jerk,
    )


__all__ = [
    "DEFAULT_LAMBDA",
    "DEFAULT_MU",
    "SYNC_ERROR_CLIP",
    "RewardConfig",
    "compute_reward",
]
