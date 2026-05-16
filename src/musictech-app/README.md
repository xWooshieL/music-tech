# musictech-app — Real-Time Score Following MVP

Standalone MVP-приложение команды MusicTech (Центральный Университет, 2026).
Слушает MIDI-вход исполнителя, в реальном времени отслеживает позицию в
партитуре (HMM / HSMM / OLTW / гибрид) и синхронно отдаёт оркестровый
аккомпанемент с подстройкой темпа.

GUI на `pygame`, ядро на чистом `numpy`. Поверх живёт скелет
RL-модуля (`musictech.rl`), который превращает классический трекер в
**anticipating agent** для упреждающего управления темпом — это
центральная идея конференционной статьи.

## Структура папки

```
musictech-app/
├── README.md                 ← этот файл
├── start.md                  ← как запустить interactive_tester
├── requirements.txt          ← numpy, mido, pygame-ce
├── LICENSE
├── .gitignore
│
├── docs/                     ← вся проектная документация
│   ├── ARCHITECTURE.md       ← слои, DTO, граф зависимостей (читать первым)
│   ├── CODE_MAP.md           ← карта .py-файлов с описанием каждого
│   ├── PROJECT_ANALYSIS.md   ← состояние / зависимости / что чинить
│   └── analysis.md           ← план RL-агента и приоритеты задач
│
├── musictech/                ← основной Python-пакет (чистый)
│   ├── core/                 ← pure-numpy ML
│   │   ├── dto.py            ← типизированные DTO между слоями
│   │   └── followers/        ← HMM, HSMM, OLTW, Hybrid
│   ├── playback/             ← TempoTracker, dispatcher, orchestra
│   ├── io/midi/              ← LiveMidiReceiver, MidiEmulator, parser
│   ├── preprocessing/        ← MIDI → score.json
│   ├── datasets/             ← synthetic + (планируется ASAP/MAESTRO)
│   ├── rl/                   ← env, state, reward, policy (скелет тезисов)
│   ├── cli/                  ← dataset_viewer, list_midi, main_legacy
│   ├── evaluation/           ← метрики (placeholder)
│   ├── calibration/          ← калибраторы (placeholder)
│   ├── pipelines/            ← high-level scenarios (placeholder)
│   ├── validation/           ← ручные валидаторы (placeholder)
│   └── audio/                ← микрофонный ввод (placeholder)
│
├── (legacy .py в корне — см. ниже разбивку)
│
├── midi/                     ← MIDI-библиотека пьес + sample-плеер
├── assets/                   ← piano + orchestra audio samples (~22 МБ)
├── generated_dataset/        ← синтетика (создаётся в рантайме)
├── notebooks/                ← Jupyter-эксперименты (9 шт.)
└── papers/                   ← локальные PDF тезисов
```

## Что лежит в корне (legacy `.py`)

Файлы, которые **физически в корне** и НЕ переехали в `musictech/` —
из соображений совместимости (на них завязаны импорты GUI и CLI).
Сгруппированы по роли:

### Тонкие shim-обёртки (5–30 строк, реэкспорт из `musictech.*`)
| Файл | Реэкспортирует |
|---|---|
| `compat.py` | `musictech.utils.compat` |
| `portable_paths.py` | `musictech.utils.portable_paths` |
| `hmm_follower.py` | `musictech.core.followers.hmm` |
| `hsmm_follower.py` | `musictech.core.followers.hsmm` |
| `oltw_follower.py` | `musictech.core.followers.oltw` |
| `hybrid_fusion.py` | `musictech.core.followers.hybrid` |
| `output_dispatcher.py` | `musictech.playback.*` |
| `midi_to_score.py` | `musictech.preprocessing.midi_to_score` |
| `midi_generator.py` | `musictech.datasets.synthetic` |
| `live_midi_receiver.py` | `musictech.io.midi.*` |
| `dataset_viewer.py` | `musictech.cli.dataset_viewer` |
| `list_midi.py` | `musictech.cli.list_midi` |
| `main.py` | `musictech.cli.main_legacy` |

### GUI (legacy — не трогать)
| Файл | Размер | Что |
|---|---:|---|
| `interactive_tester.py` | 5 KLOC | главный pygame GUI |

### Pipeline-CLI (legacy)
| Файл | Что делает |
|---|---|
| `midi_workspace.py` | импорт пьесы piano+orchestra → score.json |
| `prepare_study_mode_batch.py` | пакетная подготовка study-mode |

### Калибровка / стресс-тесты (legacy CLI)
| Файл | Что делает |
|---|---|
| `calibrate_hybrid_profile.py` | grid-search гиперпараметров |
| `autoplay_offset_benchmark.py` | бенчмарк офсет-сценариев |
| `stress_test_hybrid.py` | стресс-тесты гибрида |
| `playback_validator.py` | smoke-тест диспетчера |
| `test_input_module.py` | юнит-тесты MIDI-входа |

### Препроцессинг (legacy CLI)
| Файл | Что делает |
|---|---|
| `smart_hand_splitter.py` | левая/правая рука по pitch |

## С чего начать

Читать **в указанном порядке**:

1. **[`start.md`](start.md)** — запуск GUI за 5 команд.
2. **[`docs/PROJECT_ANALYSIS.md`](docs/PROJECT_ANALYSIS.md)** — какие модули
   честно работают, а какие заявлены, но не реализованы.
3. **[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)** — слои, DTO между
   ними, граф зависимостей. *Обязательно перед написанием нового кода.*
4. **[`docs/CODE_MAP.md`](docs/CODE_MAP.md)** — что лежит в каждом из
   ~30 модулей пакета `musictech/` и в каждом legacy-файле в корне.
5. **[`docs/analysis.md`](docs/analysis.md)** — план работ по
   RL-агенту и приоритеты задач до конференции.

## Зависимости

```
numpy
mido
pygame-ce
```

Устанавливаются из `requirements.txt`. Опционально:

- `python-rtmidi` — для live MIDI-входа;
- `matplotlib`, `pandas`, `notebook` — для ноутбуков;
- `torch`, `stable-baselines3`, `gymnasium` — для RL-обучения
  (когда будет реализовано).

## Smoke test

Из корня `musictech-app/`:

```powershell
python -c "from musictech.core.followers import HybridScoreFollower, ScoreFollowerHMM, ScoreFollowerHSMM, ScoreFollowerOLTW; from musictech.datasets.synthetic import generate_dataset; print('OK')"
```

Полная проверка трекеров на синтетике — в `notebooks/` (9 ipynb-файлов
по одному компоненту каждый).

## Что НЕ трогать без причины

- `interactive_tester.py` (5 KLOC pygame GUI) — любая перестановка ломает запуск.
- `midi/real_orchestra_player.py` (1.3 KLOC сэмплера) — самодостаточен.
- `midi_workspace.py` (0.8 KLOC pipeline) — много unicode-нормализации.

Если хочется добавить новый функционал — пиши в `musictech/`. Поверх
shim-ов в корне новое не пишем.
