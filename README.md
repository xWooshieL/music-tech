# MusicTech — Real-Time Score Following

[![landing](https://img.shields.io/badge/landing-musictech.art-10b981?style=flat-square&logo=astro&logoColor=white)](https://nizier193.github.io/music-tech/)
[![paper](https://img.shields.io/badge/paper-PDF-blue?style=flat-square)](https://github.com/Nizier193/music-tech/blob/master/article/main.pdf)
[![talk](https://img.shields.io/badge/slides-PDF-orange?style=flat-square)](https://github.com/Nizier193/music-tech/blob/master/article/presentation/presentation.pdf)
[![code](https://img.shields.io/badge/code-MVP-black?style=flat-square&logo=python)](https://github.com/Nizier193/music-tech/tree/master/src/musictech-app)

**Команда мастерской MusicTech, Центральный Университет (Т-Банк), 2026**

Репозиторий научного проекта по *real-time score following*: HMM/HSMM/OLTW-
бейзлайн + инновационный RL-модуль предсказания темпа для виртуального
оркестрового аккомпанемента. Цель — статья на конференцию
**«Научный Телеграф»** (submission — **3 мая 2026**, доклад —
17 мая 2026), позже — англоязычная версия для **ISMIR 2026** (Abu Dhabi).

---

## Что где лежит

```
music-tech/
├── README.md                ← этот файл
├── ROADMAP.md               ← план команды и календарь до 17 мая
├── .gitignore
├── ScoreFollowing.pdf       ← методичка по DTW / OLTW / HMM (PDF)
├── ScoreFollowing.tex       ← её LaTeX-исходник (87 КБ, самодостаточный)
│
├── article/                 ← всё про статью, тезисы и презентацию
│   ├── README.md            ← описание папки + ссылки на разделы
│   ├── main.tex             ← главный LaTeX-файл (REVTeX 4-2)
│   ├── main.pdf             ← собранный PDF (открывается в GitHub)
│   ├── тезисы.tex / тезисы.pdf  ← 2-страничные конференц-тезисы
│   ├── presentation/        ← beamer-презентация для «Научного Телеграфа»
│   │   ├── presentation.tex / presentation.pdf  (18 слайдов, 16:9)
│   │   ├── sections/        ← 18 .tex-фрагментов по одному слайду
│   │   ├── figures/tikz/    ← 12 TikZ-схем + 4 PGFPlots-графика
│   │   └── build.ps1, README.md
│   ├── references.bib       ← библиография (BibTeX, 35 источников)
│   ├── mainNotes.bib        ← рабочие заметки и черновые ссылки
│   ├── build.ps1            ← сборка PDF одной командой
│   ├── ismir.sty            ← резервный ISMIR-шаблон
│   ├── IEEEtran.bst         ← BibTeX-стиль (для ISMIR-режима)
│   ├── cite.sty             ← пакет цитирования
│   ├── cc_by.{eps,pdf,png}  ← логотип лицензии (нужен ISMIR-LBD)
│   │
│   ├── sections/            ← 9 разделов + 4 приложения (теоретическая статья)
│   │   ├── 01-introduction.tex
│   │   ├── 02-related-work.tex
│   │   ├── 03-formal-problem.tex
│   │   ├── 04-math-foundations.tex     ← DTW, OLTW, HMM, HSMM, SSMM, DF
│   │   ├── 05-rl-foundations.tex       ← MDP, POMDP, PPO, GAE, BC, RLHF
│   │   ├── 06-rl-for-music.tex         ← обзор Dorfer, Henkel, Peter, Wu
│   │   ├── 07-proposal.tex             ← наша гипотеза (RL-anticipation)
│   │   ├── 08-discussion.tex
│   │   ├── 09-conclusion.tex
│   │   ├── A-appendix-hmm.tex          ← Forward / Viterbi / Baum-Welch
│   │   ├── B-appendix-oltw.tex
│   │   ├── C-appendix-hsmm.tex         ← Forward для HHSMM (Cont 2010)
│   │   └── D-appendix-rl.tex           ← PPO + GAE pseudocode
│   │
│   ├── figures/
│   │   ├── example.png                 ← пример вставки растрового изображения
│   │   └── tikz/                       ← все ч/б TikZ-диаграммы (8 файлов)
│   │       ├── cnn_arch.tex
│   │       ├── demo_rubato_error.tex
│   │       ├── demo_tempo_latency.tex
│   │       ├── dtw_matrix.tex
│   │       ├── hmm_states.tex
│   │       ├── notes_example.tex       ← 5-нотный учебный пример
│   │       ├── pipeline.tex
│   │       └── rl_agent.tex
│   │
│   └── docs/                ← подборки для команды (.md)
│       ├── literature.md         ← 35+ ключевых статей со ссылками
│       ├── datasets.md           ← открытые датасеты + CU-Concerto-2026
│       ├── competitors.md        ← Cadenza Live, Antescofo и др.
│       ├── tools.md              ← Python-стек, FluidSynth, JUCE
│       └── hmm-extensions.md     ← HSMM, SSMM, DF, MML/LM3L
│
└── src/                     ← исследовательский код + MVP приложение
    ├── README.md            ← пояснение, что внутри
    └── musictech-app/       ← standalone приложение для score-following
        ├── README.md            ← точка входа в код MVP
        ├── start.md             ← как запустить interactive_tester
        ├── requirements.txt
        ├── docs/                ← вся документация
        │   ├── ARCHITECTURE.md  ← слои, DTO, граф зависимостей
        │   ├── CODE_MAP.md      ← карта файлов с описанием каждого
        │   ├── PROJECT_ANALYSIS.md
        │   └── analysis.md      ← план RL-агента
        ├── musictech/            ← Python-пакет (12 подпакетов, 30+ модулей)
        │   ├── core/followers/   ← HMM, HSMM, OLTW, Hybrid (pure-numpy)
        │   ├── playback/         ← TempoTracker, dispatcher, orchestra
        │   ├── io/midi/          ← LiveMidiReceiver, MidiEmulator, parser
        │   ├── preprocessing/    ← midi_to_score
        │   ├── datasets/         ← synthetic + (будет ASAP/MAESTRO)
        │   ├── rl/               ← env, state, reward, policy (скелет)
        │   ├── cli/              ← dataset_viewer, list_midi, main_legacy
        │   └── …
        ├── interactive_tester.py ← главное GUI (pygame, 5K строк, legacy)
        ├── midi_workspace.py     ← импорт пьесы → score.json
        ├── hybrid_fusion.py …    ← тонкие shim'ы (реэкспорт из musictech.*)
        ├── midi/                 ← MIDI-библиотека пьес + sample-плеер
        ├── assets/               ← piano + orchestra-samples (22 MB)
        ├── generated_dataset/    ← синтетика (создаётся generate_dataset)
        ├── notebooks/            ← Jupyter-эксперименты
        └── papers/               ← локальные PDF тезисов
```

---

## Быстрая навигация

### Документы команды (markdown)

- [Roadmap и план работы](ROADMAP.md) — этапы, дедлайны, ответственные.
- [Содержимое папки со статьёй](article/README.md) — что там и как собирать.
- [Литература](article/docs/literature.md) — 35+ ключевых статей со
  ссылками для скачивания.
- [Датасеты](article/docs/datasets.md) — MAESTRO, MAPS, MSMD, ASAP,
  Bach10, URMP, MusicNet, SMD, GiantMIDI, ATEPP + собственный
  CU-Concerto-2026.
- [Конкуренты и аналоги](article/docs/competitors.md) — Cadenza Live,
  MyPianist, Antescofo, Music Plus One и другие.
- [Стек инструментов](article/docs/tools.md) — Python-библиотеки,
  FluidSynth, JUCE и т.д.
- [Современные расширения HMM](article/docs/hmm-extensions.md) — HSMM,
  CRF, Neural HMM, SSMM, DF, MML/LM3L.

### Сама статья и презентация

- [Свежий PDF статьи](article/main.pdf) — открывается прямо в GitHub.
- [LaTeX-исходники статьи](article/) и [README по сборке](article/README.md).
- [Тезисы 2-страничные](article/тезисы.pdf).
- [Презентация на «Научный Телеграф»](article/presentation/presentation.pdf)
  — 18 слайдов в beamer 16:9, единый научный стиль со статьёй.
  [Описание + сборка](article/presentation/README.md).

### Приложение / код

- [src/musictech-app/](src/musictech-app/) — корень MVP.
- [start.md](src/musictech-app/start.md) — как запустить GUI за 5 команд.
- [docs/ARCHITECTURE.md](src/musictech-app/docs/ARCHITECTURE.md) — слои и DTO.
- [docs/CODE_MAP.md](src/musictech-app/docs/CODE_MAP.md) — карта всех Python-модулей.
- [docs/PROJECT_ANALYSIS.md](src/musictech-app/docs/PROJECT_ANALYSIS.md) — состояние и план фиксов.
- [docs/analysis.md](src/musictech-app/docs/analysis.md) — приоритеты задач по RL.

---

## Кто за что отвечает

| Модуль                                | Раздел статьи             | Ответственные                   |
|---------------------------------------|---------------------------|---------------------------------|
| HMM / HSMM (математика, Forward)      | §3-4, Прил. A             | Никита Новицкий, Никита Борисов |
| OLTW                                  | §4, Прил. B               | TBD                             |
| Hybrid (HSMM + OLTW)                  | §4                        | Никита Новицкий                 |
| Real-time / входные данные (MIDI)     | §3 Formal problem         | TBD                             |
| Датасеты партитур (ASAP-импортер)     | §2 Related work           | TBD                             |
| Выходной модуль (оркестровый рендер)  | §7 Proposal               | TBD                             |
| RL-модуль (изюминка)                  | §5-7, Прил. D             | Никита Новицкий + ML            |

Полное распределение и подробный план — в [ROADMAP.md](ROADMAP.md).

---

## Дедлайны

| Дата          | Событие                                                |
|---------------|--------------------------------------------------------|
| 30 апр. 2026  | Полный драфт всех разделов и приложений собран         |
| 1 мая 2026    | Финальная вычитка, проверка ссылок, формул, орфографии |
| 2 мая 2026    | Внутренний review ментора, последние правки            |
| **3 мая 2026** | **SUBMISSION статьи + тезисы на «Научный Телеграф»**  |
| 4–16 мая 2026 | Слайды, демо-видео прототипа, презентация              |
| 17 мая 2026   | Доклад на конференции                                  |
| Лето 2026     | Англоязычная версия и подача на ISMIR 2026             |

---

## Сборка PDF

```powershell
cd article
.\build.ps1
```

Подробности — в [article/README.md](article/README.md). Альтернативно:
загрузить папку `article/` в Overleaf.

---

## Запуск MVP

```powershell
cd src\musictech-app
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python interactive_tester.py --launcher
```

Подробности — в [src/musictech-app/start.md](src/musictech-app/start.md).

---

## Кому первым делом что делать

1. **Прочитать** [ROADMAP.md](ROADMAP.md) (5 минут на содержание +
   30 минут на свой раздел).
2. Посмотреть свежий [PDF статьи](article/main.pdf) — это текущее
   состояние теоретической части.
3. Открыть [`article/docs/literature.md`](article/docs/literature.md) и
   взять 2–3 статьи из своей зоны ответственности.
4. Скачать датасеты по списку в
   [`article/docs/datasets.md`](article/docs/datasets.md).
5. Поставить стек по [`article/docs/tools.md`](article/docs/tools.md).
6. Зайти в [`src/musictech-app/`](src/musictech-app/) и прочитать
   [`docs/ARCHITECTURE.md`](src/musictech-app/docs/ARCHITECTURE.md) +
   [`docs/CODE_MAP.md`](src/musictech-app/docs/CODE_MAP.md) — это карта по всему
   коду MVP.
7. Открыть свой раздел статьи в `article/sections/` и начать работу.
