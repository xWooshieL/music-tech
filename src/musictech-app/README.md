# musictech-app — Real-Time Score Following MVP

Standalone MVP-приложение команды MusicTech (Центральный Университет, 2026).
Слушает MIDI-вход исполнителя, в реальном времени отслеживает позицию в
партитуре (HMM / HSMM / OLTW / гибрид) и рассинхронно отдаёт оркестровый
аккомпанемент с подстройкой темпа.

GUI на `pygame`, ядро на чистом `numpy`. Поверх живёт скелет
RL-модуля, который превращает классический трекер в **anticipating
agent** для упреждающего управления темпом — это центральная идея
нашей конференционной статьи.

## С чего начать

| Файл                     | Зачем |
|--------------------------|-------|
| [`start.md`](start.md)   | Запуск GUI за 5 команд. |
| [`PROJECT_ANALYSIS.md`](PROJECT_ANALYSIS.md) | Что реально работает в коде, а что заявлено, но не реализовано. |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Слои, DTO между ними, граф зависимостей. **Обязательно к прочтению перед написанием нового кода.** |
| [`CODE_MAP.md`](CODE_MAP.md) | Что лежит в каждом из ~30 модулей пакета `musictech/` и в каждом legacy-файле в корне. |
| [`analysis.md`](analysis.md) | План работ по RL-агенту и приоритеты задач до конференции. |

## Структура

```
musictech-app/
├── musictech/                ← основной Python-пакет (12 подпакетов)
│   ├── core/                 ← pure-numpy ML
│   │   ├── dto.py            ← типизированные DTO между слоями
│   │   └── followers/
│   │       ├── hmm.py        ← ScoreFollowerHMM
│   │       ├── hsmm.py       ← ScoreFollowerHSMM (база боевого стека)
│   │       ├── oltw.py       ← ScoreFollowerOLTW
│   │       └── hybrid/       ← HybridScoreFollower (HSMM+OLTW+anchor)
│   ├── playback/             ← темп + диспетчер + оркестр-рендереры
│   ├── io/midi/              ← live MIDI in (receiver / emulator / parser)
│   ├── preprocessing/        ← MIDI → score.json + hand splitter (placeholder)
│   ├── datasets/             ← synthetic + ASAP/MAESTRO (placeholder)
│   ├── rl/                   ← env, state, reward, policy (скелет тезисов)
│   ├── cli/                  ← dataset_viewer, list_midi, main_legacy
│   ├── evaluation/           ← follower / tempo метрики (placeholder)
│   ├── calibration/          ← калибраторы / стресс-тесты (placeholder)
│   ├── pipelines/            ← high-level scenarios (placeholder)
│   ├── validation/           ← ручные валидаторы (placeholder)
│   └── audio/                ← микрофонный ввод (placeholder)
│
├── interactive_tester.py     ← главный pygame GUI, 5 KLOC, legacy
├── midi_workspace.py         ← импорт пьесы piano+orchestra → score.json
├── hybrid_fusion.py …        ← тонкие shim'ы (реэкспорт из musictech.*)
├── calibrate_hybrid_profile.py / autoplay_offset_benchmark.py /
│   stress_test_hybrid.py / playback_validator.py / test_input_module.py
│                             ← калибраторы и валидаторы (legacy CLI)
├── smart_hand_splitter.py / prepare_study_mode_batch.py
│                             ← preprocessing CLI (legacy)
├── midi/                     ← MIDI-библиотека пьес + DynamicOrchestraPlayer
│   ├── *.mid, *.json         ← черновые пьесы и score.json
│   ├── library/<piece>/      ← готовые импортированные пьесы
│   ├── real_orchestra_player.py  ← Philharmonia Strings сэмплер, 1.3 KLOC
│   ├── midi_splitter.py
│   └── reduce_for_single_track.py
├── assets/
│   ├── piano_samples/        ← Salamander Grand Piano (mp3)
│   └── orchestra_samples/    ← Philharmonia Strings (mp3)
├── generated_dataset/        ← синтетика (создаётся из musictech.datasets)
├── notebooks/                ← Jupyter-эксперименты
└── papers/                   ← локальные PDF тезисов
```

## Зависимости

```
numpy
mido
pygame-ce
```

Дополнительные пакеты для RL (`torch`, `stable-baselines3`, `gymnasium`),
для микрофона (`sounddevice`) и для ASAP-импортера ставятся отдельно
по мере необходимости — см. [`ARCHITECTURE.md`](ARCHITECTURE.md).

## Что не трогать без причины

См. раздел "Что про legacy" в [`CODE_MAP.md`](CODE_MAP.md). Кратко:

- `interactive_tester.py` (5 KLOC pygame GUI) — любая перестановка ломает запуск.
- `midi/real_orchestra_player.py` (1.3 KLOC сэмплера) — самодостаточен.
- `midi_workspace.py` (0.8 KLOC pipeline) — много unicode-нормализации.
