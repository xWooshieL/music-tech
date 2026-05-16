# Анализ проекта MusicTech: постановка, текущее состояние, план до MVP

## 0. Постановка задачи

### 0.1. Канонический ТЗ от заказчика

Дословные требования:

1. **Распознавание игры солиста в реальном времени** — через микрофон или MIDI, определять текущий фрагмент и темп исполнителя (алгоритм score-following).
2. **Гибкое воспроизведение оркестрового сопровождения** — синхронно с солистом, с возможностью мгновенного изменения темпа без искажений звучания. MIDI-технологии + высококачественные сэмплы.
3. **Базовый UI** — выбор произведения и части концерта, старт/стоп, регулировка громкости оркестра, начало с произвольного такта.
4. **Надёжность и производительность** — без существенных сбоев, минимальная задержка, достаточное качество синхронизации и звука для убедительной демонстрации.

### 0.2. Соответствие тезисам

Тезисы `papers/тезисы.pdf` — это **исследовательская часть** того же ТЗ. Они формализуют:

- алгоритм score-following через HMM / HSMM (пункт 1 ТЗ);
- лёгкий RL-агент опережающего предсказания темпа `a_t ∈ [0.5, 2.0]` на горизонте 200–500 мс поверх трекера (точечное улучшение пункта 2 ТЗ);
- состояние агента `s_t = (α̂_t, τ_{t-K:t}, e_{t-K:t}, φ̂(t)/N)`;
- награду `r_t = −|t_render − t_perf| − λ·L_align − μ·(a_t − a_{t-1})²`.

Генерация новых нот в тезисах **не упоминается ни разу**. В §«Положение и ценность» авторы прямо отмежёвываются от RL-Duet [10] и ReaLchords [11] как от «применения RL к генерации нового музыкального материала». Партитура оркестра в нашей задаче берётся заранее, а RL крутит только темповый коэффициент.

### 0.3. Карта соответствия «требование ↔ код в репо»

| Требование заказчика | Покрыто кодом сейчас | Что не хватает |
|---|---|---|
| Score-following, MIDI-вход | `live_midi_receiver.py`, `oltw_follower.py`, `hmm_follower.py`, `hsmm_follower.py`, `hybrid_fusion.py` | Честный HSMM по Cont 2010, RL-слой темпа (это и есть тезисы) |
| Score-following, **микрофонный вход** | **Нет** | Новая подсистема: онсет-детектор + pitch-tracker, эмиссионная модель HSMM, принимающая chroma-вектор вместо одного pitch |
| Воспроизведение оркестра, темп без искажений | `output_dispatcher.py:PygameMidiOrchestra`, `midi/real_orchestra_player.py` (Philharmonia Strings), `TempoTracker` | RL-слой темпа (тезисы), копирование velocity солиста |
| UI: выбор пьесы, старт/стоп, громкость | `interactive_tester.py --launcher`, `midi_workspace.py`, `orchestra_volume` (~114 упоминаний) | Адекватность UX, тесты |
| UI: начать с произвольного такта | `HandPracticeMidiAccompaniment.seek(target_time)` есть, но **по времени**, не по такту | Маппинг «номер такта → time / score-index», UI-элемент выбора |
| UI: выбор части концерта | Поддерживается через ручной выбор MIDI пары solo + orchestra | Метаданные «часть/движение», выбор в launcher |
| Надёжность и производительность | `calibrate_hybrid_profile.py`, `autoplay_offset_benchmark.py`, `stress_test_hybrid.py`, `playback_validator.py` | End-to-end замер latency mic → render |

Главные **дыры**: микрофон, разметка тактов, и весь RL-слой. Остальное — улучшения существующего.

### 0.4. Что есть в репо сегодня (краткая инвентаризация)

- Трекеры: `oltw_follower.py`, `hmm_follower.py`, `hsmm_follower.py`, фьюжн с anchor-recovery в `hybrid_fusion.py` (продвинутее, чем «классический трекер» из тезисов).
- Темп и рендер: `output_dispatcher.py:TempoTracker`, `PygameMidiOrchestra`, `midi/real_orchestra_player.py` с динамическим оркестром на сэмплах Philharmonia.
- Пайплайн импорта: `midi_workspace.py`, `prepare_study_mode_batch.py`, `midi_to_score.py`, `smart_hand_splitter.py`.
- UI: `interactive_tester.py` ~5.7 K строк, launcher, библиотека пьес, регулятор громкости, seek по времени.
- Калибровка/бенчмарки: `calibrate_hybrid_profile.py`, `autoplay_offset_benchmark.py`, `stress_test_hybrid.py`.
- Пример пьесы: `midi/library/rach_solo/` — 3791 score-состояние, с откалиброванным `hybrid_profile.json`.
- Сэмплы: `assets/piano_samples/salamander_mp3`, `assets/orchestra_samples/philharmonia_strings`.

То есть **скелет MVP уже стоит**. Студентам не надо начинать с нуля: они закрывают дыры и подкладывают RL под темп.

---

## 1. Ответы на три вопроса по существу

### 1.1. Какие датасеты используются и где создаются

В репо три источника, и ни один не «обучающий» в смысле градиентного обучения — потому что текущие классические трекеры обучения не требуют, у них либо нет параметров, либо параметры подбираются grid-search-ем.

**(a) Синтетика** — `midi_generator.py` → `generated_dataset/{ideal, rubato, noisy, polyphonic}.{json,mid}`, 8–13 нот гаммы. Unit-тестовый уровень.

**(b) Реальные пьесы** — `midi_workspace.py` импортирует MIDI в `midi/library/<slug>/`: создаёт `source.json` (партитура), `study_mode/{left,right}_hand.json`, `*.hybrid_profile.json`. Пример — `rach_solo`.

**(c) Autoplay-симулятор** — `autoplay_offset_benchmark.py` проигрывает партитуру обратно в трекер с возможностью внесения опечаток. На этом построена калибровка в `calibrate_hybrid_profile.py`.

**Что нужно добавить для тезисов и RL** — корпус реальных исполнений с разметкой «нота-в-ноту». Готовое решение:

- **ASAP dataset** (Foscarin et al. 2020) — 222 пьесы классического фортепиано, 1067 исполнений с note-by-note alignment;
- **MAESTRO v3** (Hawthorne 2018) — 1276 файлов, 200 ч исполнений на Disklavier, для аугментаций.

Импорт в наш формат — короткий скрипт `datasets/asap/import.py` (~150 строк), `score.json` + `performance.json` со списком `{score_index, observed_pitch, timestamp}`.

### 1.2. Формат входа в модель

Два потока: статический и динамический.

**Партитура** — JSON, схема из `midi_to_score.py`:

```198:206:d:\Projects-13-03-2026\piano\midi_to_score.py
notes.append(
    {
        "index": len(notes),
        "pitches": pitches,
        "nominal_onset": round(onset_time, 6),
        "nominal_duration": round(duration, 6),
    }
)
```

Одно «событие» = аккорд (`pitches: list[int]`), одновременные нажатия внутри `chord_epsilon=0.03 с` группируются в одно score-state.

**Исполнение** — поток MIDI `note_on` (velocity > 0), события `{"pitch": int, "timestamp": float}`. См. `dataset_viewer.load_performance`, `live_midi_receiver.LiveMidiReceiver`.

**Скрытое состояние HMM** — индекс ноты партитуры `i ∈ {0, …, N−1}`. Эмиссия — гауссиана по полутонам:

```134:137:d:\Projects-13-03-2026\piano\hmm_follower.py
def _emission_probabilities(self, observed_pitch: float) -> np.ndarray:
    deltas = (observed_pitch - self.pitches) / self.sigma
    emission = self._gaussian_norm * np.exp(-0.5 * np.square(deltas))
    return np.maximum(emission, self._tiny)
```

**Выход трекера** — индекс score-state, в котором сейчас находится солист. Не «следующая нота для оркестра», а «номер текущей ноты в готовой партитуре солиста».

### 1.3. Как обеспечиваются длительности и качество звучания

**В партитуре** хранится `nominal_duration` каждого state.

**В HSMM** переходные вероятности пересчитываются в зависимости от `ratio = elapsed / nominal`:

```348:363:d:\Projects-13-03-2026\piano\hsmm_follower.py
if ratio < 1.0:
    stay_probability = 0.82
    advance_probability = 0.18
    skip_probability = 0.0
    leap_probability = 0.0
elif ratio <= 1.5:
    phase = (ratio - 1.0) / 0.5
    stay_probability = 0.35 + (0.18 - 0.35) * phase
    advance_probability = 0.60 + (0.70 - 0.60) * phase
    skip_probability = 0.03 + (0.06 - 0.03) * phase
    leap_probability = 0.02 + (0.06 - 0.02) * phase
else:
    stay_probability = 0.12
    advance_probability = 0.68
    skip_probability = 0.08
    leap_probability = 0.12
```

Это кусочно-линейная эвристика. Cont 2010 [5] даёт правильную постановку — явные `p_i(d)` (log-normal или Gaussian с медианой = `nominal_duration` и параметром `σ_d`). Это первая точка улучшения.

**Темп оркестра** определяет `TempoTracker` (медиана по скользящему окну, deadzone, сглаживание) → `tempo_ratio` ∈ [0.25, 4.0] → передаётся в `PygameMidiOrchestra` или `real_orchestra_player.py`.

**Что регулируется сейчас**:

- **Темп**: да, через `tempo_ratio`. Сюда подключается RL по тезисам.
- **Громкость оркестра**: общий volume есть в UI (`orchestra_volume`). Per-note velocity захардкожен 76. Простое улучшение — копирование сглаженного velocity солиста.
- **Артикуляция / педаль / баланс**: только то, что в исходном оркестровом MIDI.
- **Без искажений при ускорении/замедлении**: проблема в принципе не возникает, потому что MIDI-плеер не делает audio time-stretch — каждая нота берётся как отдельный сэмпл в свой момент, растягивается только промежуток между событиями. Если когда-то добавят аудио-плеер (записанная оркестровая дорожка вместо MIDI+сэмплы) — там потребуется phase-vocoder/rubberband для pitch-preserving time-stretch.

---

## 2. План работ

План — в три уровня. Первый уровень закрывает зачёт по ТЗ заказчика, второй реализует тезисы, третий — расширения для статьи и устойчивого продукта.

### Уровень 1. MVP по ТЗ — 3–4 недели

Цель: прототип, который заказчик может потрогать и который соответствует всем 4 пунктам ТЗ.

| # | Задача | Файлы | Покрывает пункт ТЗ |
|---|---|---|---|
| 1.1 | Зафиксировать референсную пьесу (Рахманинов № 2 1-я часть или Чайковский № 1) и достать пару MIDI: solo + orchestra | — | 3 («выбор произведения и части») |
| 1.2 | `python midi_workspace.py solo.mid --orchestra-midi-file orchestra.mid --require-orchestra` | `midi_workspace.py` | 3 |
| 1.3 | Откалибровать профиль: `python calibrate_hybrid_profile.py …/source.json --level medium` | `calibrate_hybrid_profile.py` | 1, 4 |
| 1.4 | Сквозной прогон `interactive_tester.py --launcher` с живой клавиатурой | `interactive_tester.py` | 1, 2, 3 |
| 1.5 | Добавить velocity-копирование оркестра под солиста: `v_orch = clip(α·v_solo_smooth + (1−α)·v_score, 1, 127)` | `output_dispatcher.py:PygameMidiOrchestra`, `real_orchestra_player.py` | 2 |
| 1.6 | Маппинг «номер такта → нужный score-index» (через `nominal_onset` и темпо-метаданные MIDI), UI-элемент выбора стартового такта | `output_dispatcher.py`, `interactive_tester.py` | 3 («начать с произвольного такта») |
| 1.7 | End-to-end latency бенчмарк: от MIDI-in до звука оркестра, фиксируем число в README | новый `bench/latency_e2e.py` | 4 |
| 1.8 | Демо-запись 2–3 минуты + README с инструкцией | `start.md`, новый `demo/` | защита MVP |

После уровня 1 у студентов уже **зачёт по ТЗ**. Дальше идут тезисы.

### Уровень 2. Реализация тезисов — 5–7 недель

Три **независимых** трека. С командой 2–3 человека можно делать параллельно.

#### Трек 2A. Корректный HSMM (Cont 2010 + Nakamura 2015)

Текущий `hsmm_follower.py` — рабочая эвристика. Что нужно:

1. **Явные распределения длительности** `p_i(d)` для каждого score-state. Параметризация — log-normal с медианой = `nominal_duration` и параметром `σ_d` (общий по пьесе или per-state). Заменить кусочно-линейный `_transition_probabilities` на корректное forward-обновление со свёрткой по `τ`.
2. **Beam-search forward** при N ≈ 3800. Beam `k = 64` гарантированно укладывается в 20 мс.
3. **Структурные переходы** по Накамуре: repeat, insertion, deletion как явные скрытые состояния «error events».
4. **Логирование `α_t`** — пригодится для трека 2B (вход RL).

Файлы: переписать `hsmm_follower.py`, создать `evaluation/evaluate_followers.py` (вынести метрики из `autoplay_offset_benchmark.py`).

#### Трек 2B. RL-агент темпа (ядро тезисов)

Реализация по РИС. 1 и формуле (1):

1. **Датасет**. Сначала разблокировать всё: `datasets/asap/import.py` — конвертер ASAP в `score.json` + `performance.json`. Без этого треки 2A и 2B стоят.
2. **Среда (Gymnasium API)** в `rl/env.py`:
   - `reset()` загружает пару (score, performance), сбрасывает HSMM;
   - `step(a_t)` проигрывает чанк 200–500 мс с темпом `a_t`, прогоняет performance через HSMM, считает награду по формуле (1);
   - `observation` — фиксированной размерности `s_t`.
3. **Сжатие `α̂_t`**: не все N компонент, а 5–8 чисел: `max(α)`, `entropy(α)`, `argmax(α)/N`, sum of top-3 mass, top-3 индексы относительно `current_index`. Плюс K=5 последних значений темпа и эмиссионной ошибки, плюс `φ̂(t)/N`. Итого ~30 чисел на вход MLP.
4. **Стадия A: Behavior Cloning** на ASAP-исполнениях. Оракульный темп `a*_t = ΔΦ_nominal / ΔΦ_real` на скользящем окне. MLP 2×64 на регрессию `s_t → a*_t`. Без BC PPO стартует с непригодной политики.
5. **Стадия B: PPO-дообучение**. `stable-baselines3.PPO`, награда из формулы (1), стартовые гиперпараметры `λ = 1.0`, `μ = 0.5`. KL-штраф к BC-политике (Sequence Tutor [13]), иначе агент уйдёт в нефизичные политики.
6. **Симулятор солиста для онлайн-rollout**: ASAP-исполнения + параметрическое rubato (Repp 1995). Без аугментации агент переобучается на конкретных записях.
7. **Latency-аудит**: MLP 2×64 на CPU ~50 мкс, безопасно. Главный лимит — HSMM forward (см. 2A).

Файлы: `rl/env.py`, `rl/state.py`, `rl/reward.py`, `rl/policy.py`, `rl/train_bc.py`, `rl/train_ppo.py`, `rl/simulator.py`.

#### Трек 2C. Микрофонный вход (требование заказчика, **не в тезисах**)

Тезисы про микрофон не говорят. Заказчик — да. Это отдельный исследовательский risk, и его надо явно отделить от RL.

Архитектурный выбор:
- Не лезть в полный AMT (Onsets-and-Frames весит и тяжёлый по latency).
- Достаточно лёгкого детектора онсетов + классификатора pitch через CQT-вектор, который замещает MIDI-pitch на эмиссионном входе HSMM.

Минимальная реализация:

1. **Захват**: `sounddevice.InputStream`, sample-rate 22 050 или 44 100, block size ~10 мс.
2. **Онсет-детектор**: spectral flux (либо `librosa.onset.onset_detect` для прототипа, либо своя реализация на STFT для контроля latency).
3. **Эмиссия по CQT**: вместо `b_i(o) = N(observed_pitch | μ_i, σ)` сделать `b_i(chroma) = exp(−||chroma − chroma_template_i||² / 2σ²)`, где `chroma_template_i` собирается из score-pitches. Это естественное расширение текущего `_emission_probabilities`.
4. **Гибрид**: если есть и MIDI, и микрофон одновременно — fuse по принципу `b(o) = w·b_midi + (1−w)·b_audio`.

Файлы: `audio/capture.py`, `audio/onset.py`, `audio/chroma_emission.py`. Подключить к `hsmm_follower.py` через инъектируемую функцию эмиссии.

Литература по треку: Henkel 2021 [7] (real-time score following от изображения партитуры — структурно похоже), Cont 2010 [5] (там тоже audio-input), Onsets-and-Frames (Hawthorne 2018) — для понимания, не для использования.

**Важно**: если время ограничено, заказчик в требованиях написал «через микрофон **(или MIDI-вход)**». То есть MIDI-only прототип формально удовлетворяет требованию. Микрофон можно вынести в Уровень 3.

### Уровень 3. Расширения (опционально)

- Адаптация под конкретного исполнителя (fine-tune PPO в один проход после нескольких сессий — это и есть «главное преимущество RL» из §«Положение и ценность» тезисов).
- Обучаемая динамика оркестра (второй маленький MLP — регрессия velocity по велоциту солиста и контексту партитуры).
- Сравнительный benchmark с публичными score-follower-ами (Antescofo, music21, partitura).
- Polyphony / chord-density метрики при оценке на ASAP.
- Audio output: pitch-preserving time-stretch (rubberband) если когда-нибудь захотят использовать запись настоящего оркестра вместо MIDI+сэмплы.

---

## 3. Литература по приоритетам

**P0 — для трека 2A (HSMM):**
- [4] Rabiner 1989, *A Tutorial on Hidden Markov Models* — введение в HMM/forward/Viterbi.
- [5] Cont 2010, *A Coupled Duration-Focused Architecture* — **главная статья**, явные `p(d)`, anti-jitter forward.
- [6] Nakamura 2015, *Real-Time Audio-to-Score Alignment … with Errors and Arbitrary Repeats and Skips* — структурные переходы.
- [3] Dixon 2005, *On-Line Time Warping* — то, что в `oltw_follower.py`.

**P1 — для трека 2B (RL):**
- [8] Dorfer 2018, *Learning to Listen, Read, and Follow* — RL заменяет трекер целиком (baseline, не наша цель).
- [9] Peter 2023, *Online Symbolic Music Alignment with Offline Reinforcement Learning* (arXiv:2401.00466) — ближайший по идее.
- [12] Schulman 2017, *PPO*.
- [13] Jaques 2017, *Sequence Tutor* — KL-control от BC-политики, нужен в обязательном порядке для стабильности PPO.

**P2 — для трека 2C (микрофон):**
- [7] Henkel 2021, *Real-Time Music Following in Score Sheet Images* — мультимодальный score following.
- Hawthorne et al. 2018, *Onsets and Frames* — для контекста, не для прямого использования.
- Schlüter & Böck 2014, *Improved Musical Onset Detection With Convolutional Neural Networks* — для онсетов.

**P3 — контекст:**
- [10] Jiang 2020, *RL-Duet* и [11] Wu 2024, *ReaLchords* — что мы **не делаем** (генерация).
- [1] Dannenberg 1984, [2] Sakoe–Chiba 1978 — исторический контекст.

**P4 — не из библиографии, но критично:**
- Foscarin et al. 2020, *ASAP* — датасет.
- Hawthorne et al. 2018, *MAESTRO* — датасет.
- Repp B. 1995, 1998 — модели rubato для симулятора.
- Arzt 2008–2016 (диссертация и серия) — OLTW + anchor recovery, ближайший аналог `hybrid_fusion.py`.

---

## 4. Главные риски

1. **Latency честного HSMM** при N ≈ 3800. Без beam — на грани 20 мс из тезисов. С beam k=64 — безопасно. Это первый микро-эксперимент трека 2A.
2. **End-to-end latency** (input → render). Тезисный бюджет 20 мс — порог восприятия рассинхронизации; полный путь MIDI-in → HSMM → RL → MIDI-out → синтезатор/сэмплы каждый блок добавляет миллисекунды. Замерить до старта 2B.
3. **Микрофонный путь**: онсет-детектор + pitch-emission добавляют ~10–30 мс. Нужно проверить, что суммарный путь ещё укладывается.
4. **ASAP даёт alignment по нотам, но не «соло + оркестр»**. Для `t_render − t_perf` нет «эталона как должен был сыграть оркестр». Решение: считать `t_perf` по solo-MIDI, а `t_render` симулировать через детерминированный рендер orchestra-MIDI с темпом `a_t`. Аудио оркестра не требуется.
5. **Reward shaping в PPO** (`λ`, `μ`) подбирается грид-сёрчем. Закладывать 2–3 прохода.
6. **Симулятор солиста переобучает агента**. Митигация — KL-штраф к BC-политике на реальных ASAP.
7. **Маппинг «такт → score-index»** для UI-требования «начать с произвольного такта». В нашем `score.json` тактов нет, есть только `nominal_onset` и `nominal_duration`. Решения:
   - извлечь tempo-meta и `time_signature` из исходного MIDI;
   - построить таблицу `bar → time → score-index` один раз при импорте через `midi_workspace.py`;
   - сохранять её в workspace вместе с `source.json`.
8. **Дрейф офлайн-метрик vs живое ощущение**. Минимум — 5–10 живых MIDI-записей для качественной оценки на демо.

---

## 5. Что делаем прямо сейчас

Предлагаю по шагам в порядке зависимостей:

1. **Зафиксировать пьесу MVP** (например, Рахманинов № 2 1-я часть). От этого зависят все дальнейшие интеграционные тесты.
2. **Прогнать существующий `interactive_tester.py` на выбранной пьесе** — убедиться, что текущий стек физически играет, записать baseline-видео и latency-метрику.
3. **Подключить ASAP** — написать `datasets/asap/import.py`. Без датасета треки 2A и 2B стоят.
4. **Вынести метрики в `evaluation/`** — получить baseline-числа для текущих OLTW / HSMM / Hybrid.
5. **Параллельно** запустить трек 2A (HSMM по Cont) и трек 2B (BC на ASAP) — это можно делать одновременно силами двух человек.

Следующим шагом могу:

- **(а)** написать `datasets/asap/import.py` — разблокирует обучение и оценку;
- **(б)** вынести метрики из `autoplay_offset_benchmark.py` в `evaluation/` с применением к ASAP-сплитy;
- **(в)** добавить velocity-копирование в `PygameMidiOrchestra` и `real_orchestra_player.py` (первое заметное улучшение MVP);
- **(г)** добавить таблицу «такт → score-index» в `midi_workspace.py` (закрывает UI-требование «старт с такта»);
- **(д)** скелет `rl/env.py` + `rl/state.py` под спецификацию из тезисов (готовит почву под BC и PPO).
