"""Compatibility shim — see :mod:`musictech.core.followers.hmm`.

Legacy callers import ``ScoreFollowerHMM`` directly from this module;
the real class now lives in the layered package.
"""

from musictech.core.followers.hmm import ScoreFollowerHMM

__all__ = ["ScoreFollowerHMM"]


if __name__ == "__main__":
    from pathlib import Path

    from musictech.cli.dataset_viewer import load_performance
    from musictech.utils.compat import compat_zip

    dataset_dir = Path(__file__).resolve().parent / "generated_dataset"
    score_path = dataset_dir / "ideal.json"
    midi_path = dataset_dir / "ideal.mid"

    follower = ScoreFollowerHMM(score_path)
    performance = load_performance(midi_path)
    predictions = [follower.process_event(event) for event in performance]
    expected = list(range(follower.N))

    for event, predicted_index in compat_zip(performance, predictions, strict=True):
        score_pitch = int(follower.pitches[predicted_index])
        print(
            f"t={event['timestamp']:.3f}s pitch={int(event['pitch']):>3} "
            f"-> state={predicted_index:>2} score_pitch={score_pitch:>3}"
        )

    print(f"predictions: {predictions}")
    print(f"expected   : {expected}")

    if predictions != expected:
        raise SystemExit("HMM demo failed to track the ideal score correctly.")

    print("HMM demo tracked the ideal score from start to finish.")
