# Карта кода MusicTech

Документ описывает физическую структуру кода после рефакторинга 2026-04-30: пакет `musictech/` теперь является каноничным домом для всех не-GUI модулей, а корневые `*.py` сохранены как тонкие shim'ы для обратной совместимости.

Источник истины — этот файл и `ARCHITECTURE.md`. Если в коде что-то изменилось и не отражено здесь — это баг документации.

---

## 0. Что изменилось 2026-04-30

**Было** (плоский корень): 24 файла в корне репозитория, файлы по 500–5000 строк.

**Стало**:

- Весь не-GUI код переехал в `musictech/` (12 подпакетов, ~30 модулей по 50–500 строк).
- Корневые файлы превращены в shim'ы (5–30 строк, реэкспорт из `musictech.*`).
- Большие монолиты (`hybrid_fusion.py` 869, `output_dispatcher.py` 682, `live_midi_receiver.py` 309) физически разбиты на 3–6 модулей.
- Маленькие самодостаточные файлы (`hmm_follower.py` 162, `oltw_follower.py` 202, `hsmm_follower.py` 333, `midi_to_score.py` 194, `midi_generator.py` 172, `dataset_viewer.py` 90, `list_midi.py` 45, `compat.py` 12, `portable_paths.py` 53, `main.py` 192) перенесены целиком как один модуль в правильную подпапку.

**Что НЕ тронуто** (по прежнему живёт в корне как полноценный код, а не shim):

- `interactive_tester.py` (5056 строк, pygame GUI) — слишком крепко связан с pygame state и со всеми остальными модулями.
- `midi/real_orchestra_player.py` (1267 строк, сэмплер Philharmonia) — самодостаточен, имеет свой `main()`.
- `midi_workspace.py` (828 строк, pipeline-скрипт с subprocess) — куча unicode-нормализации.
- `calibrate_hybrid_profile.py` (653), `autoplay_offset_benchmark.py` (506), `stress_test_hybrid.py` (705) — большие CLI-калибраторы, ждут своего отдельного захода.
- `smart_hand_splitter.py` (497), `prepare_study_mode_batch.py` (430), `playback_validator.py` (273), `test_input_module.py` (234), `midi/midi_splitter.py` (282), `midi/reduce_for_single_track.py` (268) — оставлены как есть, но при переезде должны лечь в `musictech/preprocessing/`, `musictech/pipelines/`, `musictech/validation/`.

---

## 1. Структура `musictech/`

```
musictech/
├── __init__.py
├── utils/                          # Слой A: тонкие хелперы
│   ├── compat.py                   # ← compat.py
│   └── portable_paths.py           # ← portable_paths.py
├── core/                           # Слой B: pure-numpy ML
│   ├── dto.py                      # типизированные DTO между слоями
│   └── followers/
│       ├── hmm.py                  # ← hmm_follower.py
│       ├── hsmm.py                 # ← hsmm_follower.py
│       ├── oltw.py                 # ← oltw_follower.py
│       └── hybrid/                 # ← hybrid_fusion.py разбит на 2 модуля
│           ├── profile.py          #     load_hybrid_profile, HYBRID_PROFILE_* константы
│           └── hybrid.py           #     HybridScoreFollower (класс)
├── playback/                       # Слой C: темп + рендер
│   ├── events.py                   # ← output_dispatcher.py: DTO
│   ├── score_loader.py             # ← output_dispatcher.py: _load_score helpers
│   ├── tempo_tracker.py            # ← output_dispatcher.py: TempoTracker
│   ├── event_dispatcher.py         # ← output_dispatcher.py: ScoreEventDispatcher
│   └── orchestra/
│       ├── mock.py                 # ← output_dispatcher.py: MockOrchestraPlayer
│       └── pygame_midi.py          # ← output_dispatcher.py: PygameMidiOrchestra
├── io/                             # Слой D: вход
│   └── midi/                       # ← live_midi_receiver.py разбит на 4 модуля
│       ├── _helpers.py             #     _require_mido, _push_event, _drain_queue, mido
│       ├── receiver.py             #     LiveMidiReceiver
│       ├── emulator.py             #     MidiEmulator
│       └── parser.py               #     iter_midi_note_events (← output_dispatcher.py)
├── audio/                          # Слой D-bis: микрофонный ввод (заглушка)
├── preprocessing/                  # Слой E: MIDI → score.json
│   ├── midi_to_score.py            # ← midi_to_score.py
│   └── hand_splitter/              # заглушка под будущий перенос smart_hand_splitter
├── datasets/                       # Слой E-bis: датасеты
│   └── synthetic.py                # ← midi_generator.py
├── evaluation/                     # Слой G: метрики (заглушка)
├── calibration/                    # Слой G: калибровка (заглушка)
│   └── stress/                     # заглушка под stress_test_hybrid
├── pipelines/                      # Слой F: high-level pipelines (заглушка)
├── validation/                     # Слой G: ручная валидация (заглушка)
├── rl/                             # Слой B': RL агент
│   ├── env.py
│   ├── state.py
│   ├── reward.py
│   └── policy.py
├── cli/                            # Слой H: CLI entry points
│   ├── dataset_viewer.py           # ← dataset_viewer.py
│   ├── list_midi.py                # ← list_midi.py
│   └── main_legacy.py              # ← main.py
└── gui/                            # placeholder (interactive_tester живёт в корне)
```

Стрелка `← <файл>` означает «модуль создан из этого файла в корне».

---

## 2. Shim'ы в корне

Каждый корневой `.py` теперь либо shim (3–30 строк, реэкспорт), либо нетронутый legacy. Полный список shim'ов:

| Корневой shim | Реэкспортирует из |
|---|---|
| `compat.py` | `musictech.utils.compat` |
| `portable_paths.py` | `musictech.utils.portable_paths` |
| `hmm_follower.py` | `musictech.core.followers.hmm` |
| `hsmm_follower.py` | `musictech.core.followers.hsmm` |
| `oltw_follower.py` | `musictech.core.followers.oltw` |
| `hybrid_fusion.py` | `musictech.core.followers.hybrid` |
| `output_dispatcher.py` | `musictech.playback.*` + `musictech.io.midi.parser` |
| `midi_to_score.py` | `musictech.preprocessing.midi_to_score` |
| `midi_generator.py` | `musictech.datasets.synthetic` |
| `live_midi_receiver.py` | `musictech.io.midi.*` |
| `dataset_viewer.py` | `musictech.cli.dataset_viewer` |
| `list_midi.py` | `musictech.cli.list_midi` |
| `main.py` | `musictech.cli.main_legacy` |

Любой существующий импорт вида `from hybrid_fusion import HybridScoreFollower` продолжает работать без изменений в legacy-коде.

---

## 3. Слои (зоны ответственности)

### Слой A: Утилиты — `musictech.utils`

Без зависимостей от ML и I/O.

| Модуль | Класс / функция | Описание |
|---|---|---|
| `compat.py` | `compat_zip` | Полифилл для `zip(strict=...)` (PEP 618). |
| `portable_paths.py` | `resolve_project_path`, `project_relative_path`, `portable_command` | Нормализация путей в манифестах и subprocess-командах. |

### Слой B: Core ML — `musictech.core.followers`

Чистый `numpy`. Никаких файловых операций (кроме чтения `score.json` при инициализации), никакого MIDI, никакого `pygame`. Это **ядро**, куда подключается RL.

| Модуль | Класс | Описание |
|---|---|---|
| `hmm.py` | `ScoreFollowerHMM` | Простая HMM: гауссиана по полутонам + длительностно-зависимые stay/advance/skip. Используется только в `cli/main_legacy.py`. |
| `hsmm.py` | `ScoreFollowerHSMM` | Псевдо-HSMM: 4 перехода (stay/advance/skip/leap), переходы пересчитываются от `elapsed / nominal_duration`. **Базовый трекер в боевом стеке.** |
| `oltw.py` | `ScoreFollowerOLTW` | On-Line Time Warping (Dixon 2005) с RunCount fail-safe. Хранит две колонки DTW. |
| `hybrid/profile.py` | `load_hybrid_profile`, `HYBRID_PROFILE_TUNING_KEYS`, `HYBRID_PROFILE_FORMAT_VERSION` | Загрузка JSON-профиля настройки гиперпараметров (один на пьесу). |
| `hybrid/hybrid.py` | `HybridScoreFollower` | Фьюжн HSMM + OLTW с anchor-window recovery. Внутри держит оба трекера. **Это «классический трекер» в смысле тезисов.** |

Граф зависимостей внутри слоя:

```
oltw ─┐
      ├──→ hybrid.hybrid (HybridScoreFollower)
hsmm ─┘                       │
                              └──→ hybrid.profile (load_hybrid_profile)

hmm — изолирован, используется только cli.main_legacy
```

### Слой B': RL — `musictech.rl`

| Модуль | Назначение |
|---|---|
| `state.py` | `AlphaSummary`, `HistoryBuffer`, `encode_state` (DTO + сборка наблюдения). |
| `reward.py` | `compute_reward` (формула тезисов: `−|t_render − t_perf| − λ·L_align − μ·(a_t − a_{t−1})²`). |
| `env.py` | `ScoreFollowingEnv` (Gymnasium-совместимая среда). |
| `policy.py` | `MLPPolicy` (pure-NumPy MLP, нужен для bootstrap). |

### Слой C: Темп и оркестровый рендер — `musictech.playback`

Зависит от слоя B и от `pygame.midi` / `pygame.mixer`.

| Модуль | Класс / функция | Описание |
|---|---|---|
| `events.py` | `TempoObservation`, `DispatchEvent`, `DispatchCallback` | DTO между трекером, диспетчером и оркестром. |
| `score_loader.py` | `load_score`, `note_pitches`, `representative_pitch` | Лёгкий JSON-загрузчик (без numpy, в отличие от core followers). |
| `tempo_tracker.py` | `TempoTracker` | Расчёт `tempo_ratio` по скользящему окну score-states. Медиана + deadzone + idle reset. |
| `event_dispatcher.py` | `ScoreEventDispatcher` | Воркер-тред: получает индекс от трекера, обновляет темп, рассылает подписчикам. |
| `orchestra/mock.py` | `MockOrchestraPlayer` | Заглушка для тестов: только логирует. |
| `orchestra/pygame_midi.py` | `PygameMidiOrchestra` | Простой плеер: на каждое событие диспетчера играет один аккорд через `pygame.midi`. |

`DynamicOrchestraPlayer` (продвинутый плеер на сэмплах Philharmonia Strings) **по-прежнему живёт в `midi/real_orchestra_player.py`** — не рефакторили, см. §5.

### Слой D: I/O — `musictech.io.midi`

| Модуль | Класс / функция | Описание |
|---|---|---|
| `_helpers.py` | `_require_mido`, `_push_event`, `_drain_queue`, `mido` | Внутренние утилитки и handle на `mido`. |
| `receiver.py` | `LiveMidiReceiver` | Слушает `mido` MIDI-порт в фоновом потоке, складывает `{pitch, timestamp}` в `Queue`. |
| `emulator.py` | `MidiEmulator` | То же API, но играет события из `.mid`-файла в реальном времени. |
| `parser.py` | `iter_midi_note_events` | Оффлайн-парсер MIDI: возвращает список всех `note_on` с абсолютными timestamp'ами. |

Микрофонного ввода **нет**. Это дыра по ТЗ заказчика — см. `musictech/audio/__init__.py`.

### Слой E: Препроцессинг партитуры — `musictech.preprocessing` + `musictech.datasets`

| Модуль | Назначение |
|---|---|
| `preprocessing.midi_to_score` | `convert_to_score(midi_path, …)` → JSON. Группирует ноты в аккорды по `chord_epsilon`. |
| `datasets.synthetic` | Генерация 4 синтетических пар (`ideal/rubato/noisy/polyphonic`) для unit-тестов. |
| `preprocessing.hand_splitter` | **Заглушка**: будущий дом для `smart_hand_splitter.py`. |

Оставшиеся MIDI-препроцессоры (`midi/midi_splitter.py`, `midi/reduce_for_single_track.py`) **физически в корне**, не реструктурированы.

### Слой F: Pipelines — `musictech.pipelines`

Пустой пакет-плейсхолдер. Реальные pipeline-скрипты живут в корне: `midi_workspace.py`, `prepare_study_mode_batch.py`. В следующем заходе должны переехать сюда.

### Слой G: Калибровка / оценка / валидация

| Подпакет | Назначение | Статус |
|---|---|---|
| `musictech.calibration` | Калибраторы и стресс-тесты | пустой; CLI-скрипты `calibrate_hybrid_profile.py`, `autoplay_offset_benchmark.py`, `stress_test_hybrid.py` в корне |
| `musictech.evaluation` | Метрики follower / темпо | пустой; метрики разбросаны внутри `autoplay_offset_benchmark.py` |
| `musictech.validation` | Ручные валидаторы | пустой; `playback_validator.py`, `test_input_module.py` в корне |

Метрики **разбросаны** по этим файлам. Это первый кандидат на вынос в `musictech.evaluation`.

### Слой H: CLI и GUI — `musictech.cli` + `interactive_tester.py`

| Модуль / файл | Тип | Описание |
|---|---|---|
| `interactive_tester.py` (корень) | GUI | Главное приложение, pygame-окно. 5 KLOC. **Не трогаем.** |
| `cli/dataset_viewer.py` | CLI | Печатает пары score/performance бок-о-бок. |
| `cli/list_midi.py` | CLI | Перечисляет доступные MIDI output устройства. |
| `cli/main_legacy.py` | CLI | Старый минималистичный CLI на `ScoreFollowerHMM`. |
| `midi/real_orchestra_player.py` | CLI | Имеет собственный `main()` для запуска оркестра отдельно. **Не трогаем.** |

---

## 4. Данные

Не изменилось. Эти каталоги содержат **данные, а не код** (хотя в `midi/` лежат и .py-скрипты препроцессинга — это исторически, не реорганизуем):

| Путь | Содержимое |
|---|---|
| `assets/piano_samples/` | Salamander Grand Piano (mp3) для локального синтеза пианино. |
| `assets/orchestra_samples/` | Скачанные Philharmonia Strings. |
| `generated_dataset/` | Синтетика от `musictech.datasets.synthetic` (4 пары `*.{json, mid}`). |
| `midi/library/` | Импортированные пьесы (rach_solo, rach_solo_2). |
| `midi/*.mid`, `midi/*.json` | Сырые MIDI и черновые `score.json`. |
| `papers/` | PDF тезисов конференции. |
| `notebooks/` | Jupyter-ноутбуки с экспериментами. |

---

## 5. Что про **legacy** и что трогать нельзя

Файлы, которые **физически не двигаем и не переписываем** в этом проходе:

- `interactive_tester.py` — 5 KLOC pygame-GUI, со своим клавиатурным синтезатором и library browser. Любая перетасовка ломает запуск.
- `midi/real_orchestra_player.py` — 1.3 KLOC сэмплера со скачиванием и кэшем. Самодостаточен.
- `midi_workspace.py` — 0.8 KLOC pipeline-сценария с unicode-нормализацией и subprocess-вызовами.
- `calibrate_hybrid_profile.py`, `autoplay_offset_benchmark.py`, `stress_test_hybrid.py` — большие CLI-калибраторы.
- `smart_hand_splitter.py`, `prepare_study_mode_batch.py`, `playback_validator.py`, `test_input_module.py`, `midi/midi_splitter.py`, `midi/reduce_for_single_track.py` — оставлены как есть.

В файлы из `musictech/` можно **добавлять новое** через явные модули, не трогая существующие:

- `musictech.core.followers.hsmm` — здесь будет улучшение по Cont 2010. API `ScoreFollowerHSMM` менять нельзя — на нём держится `hybrid`.
- `musictech.core.followers.hybrid.hybrid` — менять можно только через профиль или через новые ключевые аргументы.
- `musictech.playback.tempo_tracker` — `TempoTracker` можно дополнить хуком для RL-агента, не ломая старый API.

---

## 6. Внешние зависимости (только проектное использование)

Из `requirements.txt`:

| Пакет | Где используется |
|---|---|
| `numpy` | Core ML (все трекеры), playback (tempo, dispatcher), real_orchestra_player |
| `mido` | Все MIDI-операции |
| `pygame-ce` | GUI, MIDI input/output через `pygame.midi`, аудио через `pygame.mixer` |

Не объявлено в `requirements.txt`, но опционально подхватывается:

| Пакет | Где |
|---|---|
| `python-rtmidi` | `musictech.io.midi.receiver` (через `mido`) пытается импортировать для live MIDI |

Для тезисов потребуются **новые** зависимости (см. `ARCHITECTURE.md`):

- `torch`, `stable-baselines3`, `gymnasium` — для RL;
- `sounddevice`, `librosa` (или своя реализация) — для микрофона;
- `partitura` или ручной парсер — для ASAP MusicXML.

---

## 7. Граф зависимостей одной картинкой

```
                    ┌──────────────────────────────────┐
                    │      interactive_tester.py       │
                    │  (GUI legacy в корне, не трогаем)│
                    └────────────┬─────────────────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 │ depends on (через shim'ы)     │
                 ▼                               ▼
   ┌──────────────────────────┐  ┌─────────────────────────────────┐
   │ musictech.playback.*     │  │ musictech.core.followers.hybrid │
   │  TempoTracker            │  │   HybridScoreFollower           │
   │  ScoreEventDispatcher    │  │     ┌────────┴────────┐         │
   │  PygameMidiOrchestra     │  │     ▼                 ▼         │
   └────────┬─────────────────┘  │   hsmm.py          oltw.py      │
            │                    └─────────────────────────────────┘
            ▼
   ┌──────────────────────────┐
   │ midi/real_orchestra_     │  ← в корне, не трогаем
   │   player.py              │
   │   DynamicOrchestraPlayer │
   └──────────────────────────┘

   musictech.io.midi (receiver / emulator / parser)
        └→ слушает MIDI порт или файл, кормит трекер

   musictech.rl (env / state / reward / policy)
        └→ обёртка над любым follower из musictech.core.followers
```

CLI-входы (`musictech.cli.*`, `calibrate_*`, `autoplay_*`, `stress_*` в корне) — отдельные ветки, дёргают трекер напрямую.
