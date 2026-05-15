"""Enumerate ``pygame.midi`` output devices and print them.

Useful before launching anything that talks to a hardware
synthesizer; ``pygame.midi.get_default_output_id`` returns -1 if no
device exists, and this CLI lets you confirm what is plugged in.
"""

from __future__ import annotations

import os

__all__ = ["main"]


def main() -> int:
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

    try:
        import pygame.midi
    except ModuleNotFoundError as exc:
        if exc.name == "pygame":
            print(
                "pygame is not installed. Install it into the local environment "
                "or fall back to MidiEmulator-only mode."
            )
        else:
            print(f"pygame.midi is unavailable in this build (missing module: {exc.name}).")
        return 1

    pygame.midi.init()
    try:
        found = False
        count = pygame.midi.get_count()

        print("Available MIDI output devices:")
        for device_id in range(count):
            interface, name, _is_input, is_output, _opened = pygame.midi.get_device_info(
                device_id
            )
            if not is_output:
                continue

            found = True
            device_name = name.decode("utf-8", errors="replace")
            interface_name = interface.decode("utf-8", errors="replace")
            print(f"ID {device_id}: {device_name} ({interface_name})")

        if not found:
            print("No MIDI output devices found.")
    finally:
        pygame.midi.quit()

    return 0
