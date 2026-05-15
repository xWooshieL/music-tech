"""Gymnasium environment wrapping a score follower.

The agent observes the follower's compressed posterior plus a short
history of tempo and emission errors, and outputs a tempo coefficient
``a_t ∈ [a_min, a_max]`` that the orchestra renderer would apply over
the next ``tick_seconds`` of music.

The environment is **stateful**: it maintains rolling history buffers
across ticks, advances a virtual playback clock, and re-uses the same
:class:`HybridScoreFollower` instance for the whole episode.

Gymnasium is an *optional* dependency. If ``gymnasium`` is installed the
class inherits from :class:`gymnasium.Env` and exposes the standard
``observation_space`` / ``action_space`` attributes. Otherwise we fall
back to a duck-typed class that still works inside our own training
loops but cannot be plugged directly into Stable-Baselines3. This keeps
``musictech.rl`` usable for unit tests without pulling the full RL stack.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

import numpy as np

from musictech.core.dto import (
    FollowerOutput,
    PerformanceEvent,
    RLAction,
    RLObservation,
    RLReward,
)
from musictech.rl.reward import RewardConfig, compute_reward
from musictech.rl.state import HistoryBuffer, encode_state


# ---------------------------------------------------------------------------
# Optional gymnasium base class
# ---------------------------------------------------------------------------

try:                                                    # pragma: no cover
    import gymnasium as gym
    from gymnasium import spaces

    _GymBase = gym.Env
    _HAS_GYM = True
except ImportError:                                     # pragma: no cover

    class _GymBase:  # type: ignore[no-redef]
        """Minimal stand-in for ``gymnasium.Env`` when the package is missing."""

        metadata: dict[str, Any] = {}

    spaces = None  # type: ignore[assignment]
    _HAS_GYM = False


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass
class EnvConfig:
    """Tunable knobs for :class:`ScoreFollowingEnv`.

    The defaults follow the thesis: 10 ms tick, history of 20 ticks
    (= 200 ms), tempo bounded to a half / double range.
    """

    tick_seconds: float = 0.010
    history_K: int = 20
    action_low: float = 0.5
    action_high: float = 2.0
    # Maximum number of ticks before ``truncated`` is returned by ``step``.
    max_episode_ticks: int = 60_000
    reward_config: RewardConfig = field(default_factory=RewardConfig)


# Type aliases for the pluggable callbacks the env relies on. Both let us
# inject either a real tracker (from ``musictech.core``) or a stub for
# unit tests.

FollowerStepFn = Callable[[PerformanceEvent], FollowerOutput]
"""Run one step of the follower; returns its summarized output."""

EmissionErrorFn = Callable[[PerformanceEvent, FollowerOutput], float]
"""Compute the per-step emission error e_t = -log b_{argmax(α)}(o_t)."""

RendererClockFn = Callable[[int, float], float]
"""Map (tick_index, action.tempo_coefficient) to the wall-clock time at
which the orchestra renderer would emit the *next* matched note."""

PerformerStepFn = Callable[[int], PerformanceEvent | None]
"""Pull one performance event (the soloist) for the given tick; ``None``
means the soloist stayed silent on this tick."""


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------


class ScoreFollowingEnv(_GymBase):
    """RL environment for tempo prediction.

    The environment is constructed from **callbacks** rather than concrete
    follower / renderer instances. This decouples the env (and the agent
    that uses it) from ``pygame`` / ``mido``, satisfying the constraint in
    :mod:`musictech.rl` (no audio-stack imports inside the layer).

    Typical wiring at training time (pseudocode)::

        env = ScoreFollowingEnv(
            score_length=N,
            follower_step=lambda ev: my_hybrid_follower.process_event(ev),
            emission_error=my_emission_error_fn,
            renderer_clock=my_renderer_simulator,
            performer_step=my_asap_replay,
            config=EnvConfig(),
        )

    Typical usage::

        obs, info = env.reset(seed=0)
        for _ in range(N_TICKS):
            action = policy.predict(obs)                        # in [0.5, 2.0]
            obs, reward, terminated, truncated, info = env.step(action)
            if terminated or truncated:
                break

    The environment is intentionally lightweight: it does not own the
    follower, the renderer, or the dataset. It only orchestrates ticks.
    """

    metadata = {"render_modes": [], "name": "musictech/ScoreFollowing-v0"}

    def __init__(
        self,
        score_length: int,
        follower_step: FollowerStepFn,
        emission_error: EmissionErrorFn,
        renderer_clock: RendererClockFn,
        performer_step: PerformerStepFn,
        config: EnvConfig | None = None,
    ) -> None:
        if score_length <= 0:
            raise ValueError("score_length must be positive")

        self.score_length = score_length
        self._follower_step = follower_step
        self._emission_error = emission_error
        self._renderer_clock = renderer_clock
        self._performer_step = performer_step
        self.config = config or EnvConfig()

        self._tempo_buf = HistoryBuffer(self.config.history_K, fill=1.0)
        self._emission_buf = HistoryBuffer(self.config.history_K, fill=0.0)

        self._tick_idx: int = 0
        self._last_action: RLAction | None = None
        self._last_follower_out: FollowerOutput | None = None

        # Gymnasium-compatible spaces. When gymnasium is not installed we
        # store ``None`` and don't expose them; the env still works.
        self._observation_dim = 8 + 2 * self.config.history_K
        if _HAS_GYM:
            self.observation_space = spaces.Box(
                low=-np.inf,
                high=np.inf,
                shape=(self._observation_dim,),
                dtype=np.float64,
            )
            self.action_space = spaces.Box(
                low=self.config.action_low,
                high=self.config.action_high,
                shape=(1,),
                dtype=np.float64,
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _observation_from(self, follower_out: FollowerOutput) -> RLObservation:
        return encode_state(
            follower_output=follower_out,
            tempo_history=self._tempo_buf.view(),
            emission_error_history=self._emission_buf.view(),
            score_length=self.score_length,
        )

    @staticmethod
    def _clip_action(raw: float, low: float, high: float) -> float:
        if raw < low:
            return low
        if raw > high:
            return high
        return float(raw)

    # ------------------------------------------------------------------
    # Gym API
    # ------------------------------------------------------------------

    def reset(
        self,
        *,
        seed: int | None = None,
        options: Mapping[str, Any] | None = None,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        """Reset history buffers, tick counter and last-action memory."""
        # We do not own any RNG ourselves; the soloist callback may seed
        # itself via ``options``. We forward ``seed`` for compatibility.
        del seed, options

        self._tempo_buf.reset()
        self._emission_buf.reset()
        self._tick_idx = 0
        self._last_action = None
        self._last_follower_out = None

        # Bootstrap one observation. If the soloist is silent at tick 0
        # we synthesise a "neutral" follower output so the agent can start.
        first_event = self._performer_step(0)
        if first_event is None:
            obs_vec = np.concatenate(
                (
                    np.zeros(8, dtype=np.float64),
                    self._tempo_buf.view(),
                    self._emission_buf.view(),
                )
            )
            return obs_vec, {"warmup": True}

        follower_out = self._follower_step(first_event)
        self._last_follower_out = follower_out
        obs = self._observation_from(follower_out)
        return obs.as_vector(), {"warmup": False, "model_label": follower_out.model_label}

    def step(
        self,
        action: float | np.ndarray | RLAction,
    ) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        """Advance one tick.

        Parameters
        ----------
        action
            Either a scalar tempo coefficient, a length-1 numpy array, or
            a fully-typed :class:`RLAction`.

        Returns
        -------
        ``(observation, reward, terminated, truncated, info)`` per the
        Gymnasium API.
        """
        # ---- normalise the action ------------------------------------
        if isinstance(action, RLAction):
            raw = action.tempo_coefficient
        elif isinstance(action, np.ndarray):
            raw = float(action.flat[0])
        else:
            raw = float(action)
        a = self._clip_action(raw, self.config.action_low, self.config.action_high)
        rl_action = RLAction(tempo_coefficient=a)

        self._tick_idx += 1

        # ---- pull a performer event and run the follower -------------
        perf_event = self._performer_step(self._tick_idx)
        if perf_event is None:
            # Soloist silent — re-use the last follower output and zero
            # emission error so the rolling buffer makes sense.
            follower_out = self._last_follower_out
            emission_err = 0.0
        else:
            follower_out = self._follower_step(perf_event)
            self._last_follower_out = follower_out
            emission_err = float(self._emission_error(perf_event, follower_out))

        if follower_out is None:
            # Should not happen after the first call to reset(), but be safe.
            obs_vec = np.concatenate(
                (
                    np.zeros(8, dtype=np.float64),
                    self._tempo_buf.view(),
                    self._emission_buf.view(),
                )
            )
            return obs_vec, 0.0, False, True, {"reason": "no follower output"}

        # ---- update history buffers ----------------------------------
        self._tempo_buf.push(a)
        self._emission_buf.push(emission_err)

        # ---- compute reward ------------------------------------------
        t_perf = perf_event["timestamp"] if perf_event is not None else follower_out.timestamp
        t_render = float(self._renderer_clock(self._tick_idx, a))
        reward_components = compute_reward(
            action=rl_action,
            previous_action=self._last_action,
            t_render=t_render,
            t_perf=t_perf,
            alignment_loss=emission_err,
            config=self.config.reward_config,
        )
        self._last_action = rl_action

        # ---- build the observation -----------------------------------
        observation = self._observation_from(follower_out)

        # ---- termination conditions ----------------------------------
        terminated = follower_out.score_index >= self.score_length - 1
        truncated = self._tick_idx >= self.config.max_episode_ticks

        info: dict[str, Any] = {
            "model_label": follower_out.model_label,
            "score_index": follower_out.score_index,
            "tick": self._tick_idx,
            "reward_sync": reward_components.sync_error,
            "reward_align": reward_components.alignment_error,
            "reward_jerk": reward_components.tempo_jerk,
        }

        return observation.as_vector(), float(reward_components.total), terminated, truncated, info

    def render(self) -> None:                                    # pragma: no cover
        """No-op: this environment is headless by design."""
        return None

    def close(self) -> None:                                     # pragma: no cover
        """No-op: external resources are not owned by the env."""
        return None


__all__ = [
    "EmissionErrorFn",
    "EnvConfig",
    "FollowerStepFn",
    "PerformerStepFn",
    "RendererClockFn",
    "ScoreFollowingEnv",
]
