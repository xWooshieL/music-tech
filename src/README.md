# src/ — research code + MVP

Здесь живут две большие сущности:

1. **`musictech-app/`** — *standalone* MVP-приложение для real-time
   score-following (HMM + OLTW + Hybrid + GUI на pygame). Это рабочий
   прототип, который мы будем демонстрировать на «Научном Телеграфе»
   и затем превращать в C++/Python desktop-приложение по плану из
   [../ROADMAP.md](../ROADMAP.md).

2. *(будущее)* — Jupyter-ноутбуки с экспериментами, обучение RL-агента
   на ASAP, замеры baseline-метрик. Сейчас они лежат внутри
   `musictech-app/notebooks/`, но в чистой long-term раскладке должны
   подняться сюда.

## Что внутри `musictech-app/`

Полный обзор — в этих файлах (читать в указанном порядке):

- **[`musictech-app/start.md`](musictech-app/start.md)** — как запустить
  GUI за 5 команд.
- **[`musictech-app/PROJECT_ANALYSIS.md`](musictech-app/PROJECT_ANALYSIS.md)**
  — какие модули уже есть, какие куски *честно работают*, а какие
  заявлены, но не реализованы.
- **[`musictech-app/ARCHITECTURE.md`](musictech-app/ARCHITECTURE.md)** —
  слои, DTO между слоями, граф зависимостей. **Главное** для новых
  разработчиков.
- **[`musictech-app/CODE_MAP.md`](musictech-app/CODE_MAP.md)** — карта
  всех Python-файлов с описанием каждого.
- **[`musictech-app/analysis.md`](musictech-app/analysis.md)** — план
  работ по RL-модулю и приоритеты задач до конференции.

## Структура `musictech-app/`

```
musictech-app/
├── musictech/                ← Python-пакет (12 подпакетов, ~30 модулей)
│   ├── core/followers/       ← HMM, HSMM, OLTW, Hybrid (pure-numpy)
│   ├── playback/             ← TempoTracker, dispatcher, orchestra players
│   ├── io/midi/              ← LiveMidiReceiver, MidiEmulator, parser
│   ├── preprocessing/        ← midi_to_score, hand_splitter (placeholder)
│   ├── datasets/             ← synthetic + ASAP/MAESTRO (placeholder)
│   ├── rl/                   ← env, state, reward, policy (скелет тезисов)
│   ├── cli/                  ← dataset_viewer, list_midi, main_legacy
│   ├── evaluation/           ← метрики (placeholder)
│   ├── calibration/          ← калибраторы (placeholder)
│   ├── pipelines/            ← high-level сценарии (placeholder)
│   ├── validation/           ← ручные валидаторы (placeholder)
│   └── audio/                ← микрофонный ввод (placeholder)
│
├── interactive_tester.py     ← главный GUI, pygame, 5K строк, legacy
├── midi_workspace.py         ← импорт пьесы → score.json (CLI)
├── hybrid_fusion.py …        ← тонкие shim'ы (3-30 строк, реэкспорт)
├── calibrate_hybrid_profile.py / autoplay_offset_benchmark.py / …
│                             ← калибраторы и стресс-тесты (legacy)
├── midi/                     ← пьесы (MIDI), sample-плеер
├── assets/                   ← piano + orchestra audio samples
├── generated_dataset/        ← синтетика (создаётся в рантайме)
├── notebooks/                ← Jupyter-эксперименты
├── papers/                   ← локальные PDF тезисов
└── requirements.txt
```

Подробное описание того, какой файл что делает и куда писать новое — в
[`musictech-app/CODE_MAP.md`](musictech-app/CODE_MAP.md) и
[`musictech-app/ARCHITECTURE.md`](musictech-app/ARCHITECTURE.md).
