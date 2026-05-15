# Notebooks

Распутывание кодовой базы MusicTech по смысловым блокам. Каждый ноутбук —
короткий, фокусированный, можно потыкать переменные и сразу увидеть выход.

Никакого GUI, никаких pygame-окон. Только данные, модели и графики.

## Setup

Установить недостающие зависимости (один раз):

```bash
.\.venv\Scripts\python.exe -m pip install matplotlib pandas notebook
```

Запустить Jupyter из корня проекта:

```bash
.\.venv\Scripts\jupyter.exe notebook notebooks/
```

Импорты в ноутбуках предполагают, что текущая директория — корень репо
(где лежат `hmm_follower.py`, `hsmm_follower.py` и т.д.). Каждый ноутбук
явно добавляет корень в `sys.path` в первой ячейке, так что Jupyter из
любой директории тоже сработает.

## Порядок

| # | Файл | Что внутри |
|---|---|---|
| 01 | `01_datasets.ipynb` | Что есть в репо: `generated_dataset/`, `midi/library/`. Какие пары score↔performance. |
| 02 | `02_score_format.ipynb` | Формат `score.json`: поля, аккорды, длительности. Визуализация рахманиновской партитуры. |
| 03 | `03_performance_midi.ipynb` | Что приходит на вход в realtime. MIDI-события, сравнение с номиналом, rubato. |
| 04 | `04_oltw.ipynb` | OLTW (Dixon 2005). Пошагово прогоняем на `ideal`, `rubato`, `noisy`. Графики предсказанного индекса. |
| 05 | `05_hmm.ipynb` | HMM (Rabiner 1989). Forward по pitch + длительности. Тепловая карта α по времени. |
| 06 | `06_hsmm.ipynb` | HSMM (по Cont 2010, эвристика). Длительностно-зависимые переходы stay/advance/skip/leap. |
| 07 | `07_hybrid.ipynb` | `HybridScoreFollower`. Когда переключается с HSMM на OLTW. Якорный resync. |
| 08 | `08_tempo.ipynb` | `TempoTracker`. Оценка `tempo_ratio` из последовательности score-states и timestamps. |
| 09 | `09_rl_skeleton.ipynb` | DTO из `musictech.core.dto`. `RLObservation`, `RLAction`, `RLReward`. Каркас под обучение. |

## Что НЕ делается в ноутбуках

- Запуск GUI (`interactive_tester.py`).
- Калибровка профилей (`calibrate_hybrid_profile.py`) — это многочасовой грид-сёрч.
- Импорт пьес (`midi_workspace.py`) — это CLI-сценарий.
- Обучение RL (`train_bc.py`, `train_ppo.py`) — это уже скрипты, не ноутбуки.

Ноутбуки нужны чтобы **понять** каждый компонент и видеть его выход на
конкретных данных. После них пишется production-код в `musictech/`.
