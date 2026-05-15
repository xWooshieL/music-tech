"""Command-line entry points.

Thin scripts that wire libraries from other layers (followers,
playback, datasets, preprocessing) to argparse. Each module exposes a
``main()`` callable so the root-level shim files can stay one-liners.

Modules:

- :mod:`.dataset_viewer` — side-by-side score / performance dump.
- :mod:`.list_midi`       — enumerate ``pygame.midi`` output devices.
- :mod:`.main_legacy`     — old realtime HMM CLI (``main.py``).
"""

__all__: list[str] = []
