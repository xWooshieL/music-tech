# First Start

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
rm -f interactive_tester_settings.json
python3 interactive_tester.py --launcher
```

# New User Flow

1. In the first-run wizard, leave `Orchestra Engine` on `Local samples`.
2. For `Digital Piano Input`, choose the real keyboard or digital piano input.
3. Do not choose `IAC`, `Logic Pro Virtual Out`, `Network Session`, or `Loopback` as the piano input.
4. Save the settings and continue.

# Import Piano + Orchestra

1. Open `Orchestra / Full Score`.
2. Click `Load MIDI Pair`.
3. Select the piano MIDI file.
4. Select the orchestra MIDI file.
5. Wait for the workspace import to finish and launch automatically.

# Manual Commands

```bash
python3 interactive_tester.py --launcher
python3 midi_workspace.py --list
python3 midi_workspace.py /absolute/path/to/piano.mid --orchestra-midi-file /absolute/path/to/orchestra.mid --require-orchestra
```

# Logic / MIDI Output

Use this only after local samples are already working.

```bash
python3 interactive_tester.py --launcher
```

Then switch the orchestra engine to `Logic / MIDI`, keep the piano input on the physical keyboard input, and route only the orchestra output to IAC / Logic.
