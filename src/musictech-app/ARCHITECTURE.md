# Архитектура MusicTech

Документ описывает **целевое деление по слоям**, поток данных от MIDI-ввода до колонок, типы данных между блоками (DTO), и куда писать новый код для реализации тезисов и требований заказчика.

В паре с `CODE_MAP.md` (там — физические файлы и зоны ответственности).

---

## 1. Главный принцип реорганизации

Мы **не переносим** существующие файлы. У них слишком много CLI-входов, тестов и взаимных импортов; любое массовое перемещение ломает работу.

Вместо этого поверх существующего кода накладывается **новый пакет `musictech/`**, который через тонкие реэкспорты собирает разрозненные модули в слои. Старый код продолжает работать как раньше; **новый код пишется сразу в `musictech/`** в правильный слой.

```
piano/                              ← корень репо
├── interactive_tester.py          ← legacy, не трогать
├── hybrid_fusion.py               ← legacy, не трогать
├── ... все остальные .py          ← legacy
│
└── musictech/                     ← новый пакет, целевая структура
    ├── core/                      ← ядро ML (тут уже работают трекеры через shim)
    │   ├── __init__.py            ← реэкспорт ScoreFollower*, TempoTracker
    │   └── dto.py                 ← типизированные DTO между слоями
    │
    ├── rl/                        ← новый код для RL-агента из тезисов
    ├── datasets/                  ← новый код для ASAP/MAESTRO импортёров
    ├── evaluation/                ← новый код для метрик
    └── audio/                     ← новый код для микрофона (ТЗ заказчика)
```

Если потом захотим физически переехать — у нас уже будет чистый namespace и мы будем точно знать что куда переносить.

---

## 2. Слои сверху вниз

```
┌─────────────────────────────────────────────────────────────────────────┐
│ L7. GUI / CLI / Launcher                                                 │
│ interactive_tester.py, main.py, dataset_viewer.py, …                     │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────────────┐
│ L6. Pipelines (импорт пьес, калибровка, бенчмарки)                       │
│ midi_workspace.py, prepare_study_mode_batch.py, calibrate_*,             │
│ autoplay_*, stress_*, playback_validator.py                              │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────────────┐
│ L5. Orchestra Playback (рендереры)                                       │
│ output_dispatcher.PygameMidiOrchestra, midi.real_orchestra_player        │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────────────┐
│ L4. Tempo control                                                         │
│ output_dispatcher.TempoTracker  ← [новое] ← musictech.rl.policy           │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────────────┐
│ L3. Score Follower (Core ML, numpy only)                                  │
│ HybridScoreFollower → {ScoreFollowerHSMM, ScoreFollowerOLTW}              │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────────────┐
│ L2. Input pipelines                                                       │
│ live_midi_receiver, MidiEmulator,                                         │
│ [новое] musictech.audio.{capture, onset, chroma_emission}                 │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────────────┐
│ L1. Score documents (статика)                                             │
│ score.json (наш формат), MIDI-файлы, bar-to-index map                     │
└──────────────────────────────────────────────────────────────────────────┘
```

Поток данных в realtime — снизу вверх для **входа** (MIDI-нота → трекер → темп → оркестр), и сверху вниз для **управления** (GUI → pipelines → калибровка). RL-агент сидит сбоку от L4 и читает состояние L3.

---

## 3. DTO между слоями

Сейчас почти весь обмен между модулями — `dict[str, Any]` или позиционные кортежи. Это создаёт мутность, на которую жалуется любой новый разработчик. Заводим явные DTO в `musictech/core/dto.py`. Старый код продолжает использовать словари; новый код использует DTO; при необходимости — конвертеры.

### 3.1. Статика партитуры

```python
class ScoreNote(TypedDict):
    index: int                     # порядковый номер state в score
    pitches: list[int]             # MIDI-ноты в аккорде (или [pitch] для монофонии)
    nominal_onset: float           # секунды от начала пьесы
    nominal_duration: float        # секунды

class ScoreDocument(TypedDict):
    piece_name: str
    notes: list[ScoreNote]
    # опционально, появятся:
    bar_to_index: dict[int, int]   # номер такта → индекс ноты (для UI «начать с такта»)
    tempo_map: list[TempoMarker]   # темпо-карта из MIDI
```

### 3.2. Realtime событие исполнителя

```python
class PerformanceEvent(TypedDict):
    pitch: int                     # MIDI-нота (или -1 для chroma-эмиссии)
    timestamp: float               # секунды от старта сессии (монотонные)
    velocity: int                  # 1..127 (для копирования в оркестр)
    chroma: np.ndarray | None      # 12-вектор, опционально (для микрофона)
```

В существующем коде это `Dict[str, Union[float, int]]`. Совместимость:

```python
def to_performance_event(d: dict) -> PerformanceEvent:
    return {"pitch": int(d["pitch"]),
            "timestamp": float(d["timestamp"]),
            "velocity": int(d.get("velocity", 76)),
            "chroma": d.get("chroma")}
```

### 3.3. Выход трекера

```python
@dataclass
class FollowerOutput:
    score_index: int               # текущий индекс state
    alpha_summary: AlphaSummary    # сжатие α_t для RL
    confidence: float              # max(α_t)
    model_label: str               # "hsmm" | "oltw" | "hybrid"
    timestamp: float
    resynced: bool                 # был ли якорный resync на этом шаге

@dataclass
class AlphaSummary:
    max_value: float
    entropy: float
    argmax_normalized: float       # argmax(α)/N
    top3_indices: list[int]        # относительно current_index
    top3_mass: float
```

`AlphaSummary` — это и есть `α̂_t` из тезисов. 7 чисел вместо вектора длины N.

### 3.4. Темп

```python
@dataclass
class TempoEstimate:
    ratio: float                   # 1.0 = номинальный, >1 = быстрее
    confidence: float              # на сколько надёжна оценка
    history: tuple[float, ...]     # последние K значений
    variance: float
```

### 3.5. RL-интерфейс (формула 1 тезисов)

```python
@dataclass
class RLObservation:
    alpha: AlphaSummary
    tempo_history: np.ndarray      # τ_{t-K:t}
    emission_error_history: np.ndarray   # e_{t-K:t}
    score_position_normalized: float     # φ̂(t)/N

@dataclass
class RLAction:
    tempo_coefficient: float       # a_t ∈ [0.5, 2.0]

@dataclass
class RLReward:
    total: float
    sync_error: float              # -|t_render - t_perf|
    alignment_error: float         # -λ * L_align
    tempo_jerk: float              # -μ * (a_t - a_{t-1})²
```

Это ровно то, что описано в `papers/тезисы.pdf` формула (1). Разбиение на компоненты нужно для диагностики PPO.

---

## 4. Pipeline в realtime (что когда вызывается)

```
1. Keyboard / MIDI-port / Microphone
        │
        ▼ raw bytes/audio
2. musictech.io  (live_midi_receiver | musictech.audio.capture)
        │
        ▼ PerformanceEvent
3. musictech.core.followers.HybridScoreFollower.process_event()
        │
        ▼ FollowerOutput (+ внутренний α_t)
4. musictech.core.tempo.TempoTracker.update()
        │  ─── [новое] ──→  musictech.rl.policy.predict(s_t) ──→ RLAction
        ▼ TempoEstimate (a_t)
5. musictech.playback (PygameMidiOrchestra | DynamicOrchestraPlayer)
        │
        ▼ MIDI/audio out
6. Звуковая карта
```

RL-агент **врезается между 3 и 4**, не заменяя `TempoTracker`, а корректируя его выход на горизонте 200–500 мс. Архитектурно агент читает `(FollowerOutput.alpha_summary, recent tempo, recent emission_error, position_normalized)` и выдаёт `RLAction.tempo_coefficient`, который `TempoTracker` использует как hint/prior.

---

## 5. Где жить новому коду (тезисы + ТЗ)

### 5.1. `musictech/rl/` — ядро тезисов

Файлы (пока их нет, **сюда писать**):

| Файл | Что содержит |
|---|---|
| `dto.py` (или импорт из `musictech.core.dto`) | RLObservation, RLAction, RLReward |
| `state.py` | `encode_state(follower_output, tempo_history) -> RLObservation` |
| `reward.py` | `compute_reward(action, prev_action, follower_output, performance_event) -> RLReward` |
| `env.py` | `class ScoreFollowingEnv(gymnasium.Env)` |
| `policy.py` | MLP 2×64 на PyTorch, fixed-latency inference |
| `simulator.py` | Параметрический rubato-симулятор солиста (Repp 1995) |
| `train_bc.py` | Behavior cloning на ASAP-исполнениях, оракульный темп `a*_t = ΔΦ_nominal / ΔΦ_real` |
| `train_ppo.py` | PPO-дообучение с KL-штрафом к BC (Sequence Tutor [13]) |

### 5.2. `musictech/datasets/` — корпуса с разметкой

| Файл | Что содержит |
|---|---|
| `asap.py` | `import_asap(asap_root, out_root)` — ASAP → `score.json` + `performance.json` со списком `{score_index, observed_pitch, timestamp}` |
| `maestro.py` | (опционально) MAESTRO для аугментаций |
| `manifest.py` | Чтение/запись `datasets/<corpus>/manifest.json` |
| `synthetic.py` | Тонкая обёртка над `midi_generator.py` (через shim) |

### 5.3. `musictech/evaluation/` — метрики

Сейчас метрики живут внутри `autoplay_offset_benchmark.py` и калибратора. Выносим:

| Файл | Что содержит |
|---|---|
| `follower_metrics.py` | alignment accuracy, onset-error @ 50/100/250 мс, recovery latency |
| `tempo_metrics.py` | tempo jerk, render-perf delay (требует симулятор рендера) |
| `runners.py` | `evaluate_follower_on_dataset(follower_factory, dataset) -> Report` |
| `report.py` | DTO для отчётов + сериализация в JSON/CSV |

### 5.4. `musictech/audio/` — микрофонный вход (ТЗ заказчика)

Не часть тезисов, но требование заказчика. Только если осталось время.

| Файл | Что содержит |
|---|---|
| `capture.py` | `class MicrophoneCapture` поверх `sounddevice.InputStream`, тот же API что `LiveMidiReceiver` |
| `onset.py` | Spectral-flux детектор онсетов |
| `chroma_emission.py` | Альтернативная эмиссионная функция для HSMM по chroma-вектору |

### 5.5. `musictech/core/` — ядро ML (уже здесь)

Содержимое после первой итерации:

| Файл | Что содержит |
|---|---|
| `__init__.py` | Реэкспорт `ScoreFollowerOLTW`, `ScoreFollowerHMM`, `ScoreFollowerHSMM`, `HybridScoreFollower`, `TempoTracker` |
| `dto.py` | Все DTO из раздела 3 этого документа |

Сюда же позже переедет (или будет реэкспортирован) улучшенный HSMM по Cont 2010.

---

## 6. Что НЕ трогаем

| Файл | Причина |
|---|---|
| `interactive_tester.py` | 5К строк GUI, монолит, потерять любой компонент = сломать запуск. |
| `midi/real_orchestra_player.py` | 1.3К строк сэмплера с скачиванием/кэшем Philharmonia. Самодостаточен. |
| `midi_workspace.py` | 0.8К строк pipeline-импортёра, активно вызывается из GUI. |
| `prepare_study_mode_batch.py` | вызывается из `midi_workspace.py`. |
| `hybrid_fusion.py` | публичный API нужен `interactive_tester.py`, всем калибраторам и `real_orchestra_player.py`. |

Все остальные изменения — только аддитивные, без переименований.

---

## 7. Шаги реализации (последовательность)

С учётом приоритета «доделать до тезисов как можно проще»:

1. **Шаг 1 (готово в этом коммите).** Создать `musictech/` со слоями. В `core/` реэкспортировать существующие трекеры и `TempoTracker`. Положить DTO в `core/dto.py`. В `rl/`, `datasets/`, `evaluation/`, `audio/` положить `__init__.py` с описанием «куда писать».

2. **Шаг 2.** Написать `musictech/datasets/asap.py` — импортёр ASAP в наш формат. **Это блокер** для всего обучения. ~150 строк.

3. **Шаг 3.** Вынести метрики в `musictech/evaluation/follower_metrics.py`. Получить baseline-числа для `HybridScoreFollower` на ASAP. ~200 строк.

4. **Шаг 4.** Написать `musictech/rl/state.py` + `env.py` + `simulator.py`. Поверх существующего `HybridScoreFollower`, без правки последнего. ~300 строк всего.

5. **Шаг 5.** `musictech/rl/train_bc.py` — обучить BC на ASAP, получить начальную политику.

6. **Шаг 6.** `musictech/rl/train_ppo.py` — PPO-дообучение с KL-штрафом.

7. **Шаг 7 (опционально).** `musictech/audio/` — микрофон.

8. **Шаг 8 (только если останется время и желание).** Подключить RL-политику в `output_dispatcher.TempoTracker` как опциональный hint. Включается флагом, по умолчанию выключено.

Шаги 4–6 могут идти параллельно с улучшением HSMM по Cont 2010 (трек 2A из `analysis.md`).

---

## 8. Контракты, которые нельзя нарушать

При написании нового кода:

- **Realtime hot path** (`process_event` → `update` → broadcast) должен укладываться в **20 мс** end-to-end на CPU. Замерять обязательно перед добавлением RL-инференса.
- **Никаких блокирующих I/O** в realtime-пути (никаких `open(...)`, `Path.exists()`, `mido.MidiFile(...)` внутри `process_event`).
- **Никакого `pygame` или `mido`** внутри `musictech/core/` и `musictech/rl/`. Эти модули должны быть тестируемыми на чистом numpy без аудио-стека.
- **Score.json формат менять нельзя** — на нём держатся откалиброванные `*.hybrid_profile.json` для всех пьес в `midi/library/`. Если нужно расширить — только аддитивно (новые опциональные поля).

---

## 9. Зависимости, которые добавятся

В `requirements.txt` пока минимум (`numpy`, `mido`, `pygame-ce`). Для тезисов добавим:

```
torch>=2.1               # для policy и BC
stable-baselines3>=2.3   # PPO
gymnasium>=0.29          # env API
```

Для микрофона (опционально):

```
sounddevice>=0.4
librosa>=0.10            # либо своя реализация на numpy
```

Для ASAP-импортёра, скорее всего, **ничего не надо** — формат там простой (текстовые аннотации + MIDI). Если решим парсить MusicXML, можно подключить `partitura>=1.5`.
