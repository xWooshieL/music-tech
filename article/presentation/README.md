# Презентация MusicTech — «Научный Телеграф» 2026

Доклад на 20--25 минут, **36 страниц**. Сделан в фирменном стиле
команды (Madrid + seahorse, pdflatex, T2A), как
`HW_3_PRESENTATION.tex` и `HW_10_PRESENTATION_NP.tex` --- те же
шрифты, та же организация секций, тот же подход к пошаговому
выводу математики и численным примерам.

## Структура

```
article/presentation/
├── presentation.tex              ← preamble + \input{sections/...}
├── presentation.pdf              ← собранный PDF (36 страниц, 1.4 МБ)
├── build.ps1                     ← два прогона pdflatex
├── README.md
├── sections/                     ← 25 .tex-фрагментов
│   ├── 00-introduction.tex       (актуальность / проблема / подход / цель)
│   ├── 02-problem.tex
│   ├── 03-pipeline.tex
│   ├── 04-score-format.tex
│   ├── 05-performance.tex
│   ├── 06a-dtw-derivation.tex    ← ВЫВОД DTW recurrence + Беллман
│   ├── 06-oltw.tex
│   ├── 06b-oltw-example.tex      ← численный пример DP-таблицы
│   ├── 07-hmm.tex
│   ├── 07a-hmm-forward.tex       ← ВЫВОД Forward-формулы
│   ├── 07b-hmm-example.tex       ← численный пример Forward
│   ├── 08-hsmm.tex
│   ├── 09-hybrid.tex
│   ├── 10-baseline-results.tex
│   ├── 11-baseline-limits.tex
│   ├── 12-proposed-architecture.tex
│   ├── 12a-mdp-formal.tex        ← MDP-формализация (S, A, P, R, γ)
│   ├── 13-rl-math.tex
│   ├── 13a-reward-derivation.tex ← обоснование формулы награды
│   ├── 14-training.tex
│   ├── 15-simulator.tex
│   ├── 16-roadmap.tex
│   ├── 17-conclusion.tex
│   ├── 18-thanks.tex
│   └── 19-references.tex         ← 16 источников (Rabiner, Dixon, Cont,
│                                   PPO, GAE, Sutton, RL-Duet, ASAP, ...)
├── figures/
│   ├── cu_logo.png               ← чёрный логотип ЦУ (для \logo{})
│   ├── generate_plots.py
│   ├── png/                      ← 5 ручных схем
│   ├── generated/                ← 5 ч/б PDF из реальных данных
│   └── tikz/                     ← 7 TikZ-схем
└── template/                     ← (не используется текущей сборкой,
                                    наследие предыдущей итерации)
```

## Сборка

```powershell
cd article/presentation
.\build.ps1
```

или вручную:

```powershell
pdflatex -interaction=nonstopmode presentation.tex
pdflatex -interaction=nonstopmode presentation.tex
```

Два прогона нужны для `\tableofcontents` и счётчиков секций.
Результат --- `presentation.pdf`, 36 страниц, ~1.4 МБ.

Перегенерация графиков:

```powershell
cd article/presentation/figures
python generate_plots.py
```

## Логика доклада

| Слайд | Тема | Что нового |
|------:|------|------------|
|   1   | Титульник                     |   |
|   2   | Структура (TOC)               |   |
| **3** | **Введение**                  | Актуальность / Проблема / Подход / Цель |
|   4   | Проблема: аккомпаниатор       | `png/world_view.png` |
|   5   | Pipeline системы              | `png/system_pipeline.png` |
|   6   | Outline                       | — |
|   7   | `score.json` формат           | `generated/rach_solo_pitch_time.pdf` (3797 state) |
|   8   | Performance MIDI / rubato     | `generated/rubato_deviations.pdf` |
|   9   | Outline                       | — |
|**10** | **DTW: определение path**     |   |
|**11** | **DTW: вывод recurrence**     | Принцип Беллмана → формула в боксе |
|  12   | OLTW                          | `png/oltw_dp.png` |
|**13** | **OLTW: численный пример t=1**| 5-нотная гамма, DP-таблица |
|**14** | **OLTW: пример t=2,3,4**      | продолжение |
|  15   | HMM                           | `png/hmm_chain.png` |
|**16** | **HMM: вывод Forward (1/2)**  | Инициализация + индукция |
|**17** | **HMM: вывод Forward (2/2)**  | Цепной разбор → формула + сложность |
|**18** | **HMM Forward: пример t=1**   | $\sigma{=}2$, gauss эмиссии |
|**19** | **HMM Forward: пример t=2**   | prior / эмиссия / нормировка → confidence |
|  20   | HSMM                          | `tikz/hsmm-duration.tex` |
|  21   | Hybrid Fusion                 | `png/hybrid_fusion.png` |
|  22   | Результаты baseline           | OLTW траектории + α-heatmap |
|  23   | Outline                       | — |
|  24   | Почему baseline недостаточно  | `tikz/reactive-vs-anticip.tex` |
|  25   | Outline                       | — |
|  26   | Предлагаемая архитектура (РИС.1) | `tikz/proposed-arch.tex` |
|**27** | **MDP-формализация**          | $\langle\mathcal{S}, \mathcal{A}, P, R, \gamma\rangle$ |
|  28   | Математика RL-слоя            | формула (1) тезисов |
|**29** | **Откуда формула награды (1/2)**| 3 цели → линейная комбинация |
|**30** | **Откуда формула награды (2/2)**| L1 vs L2, регуляризация, гладкость |
|  31   | Outline                       | — |
|  32   | Обучение BC → PPO             | `tikz/training-pipeline.tex` |
|  33   | Симулятор                     | `tikz/simulator-loop.tex` |
|  34   | Outline                       | — |
|  35   | Что готово и план             | `tikz/roadmap-timeline.tex` |
|  36   | Выводы                        |   |
|  37   | Outline (Литература)          | — |
|**38** | **Литература (классика)**     | Rabiner, Dixon, Cont, Nakamura, Müller |
|**39** | **Литература (RL)**           | PPO, GAE, Sutton, Sequence Tutor, RLHF |
|**40** | **Литература (RL+датасеты)**  | Dorfer, Peter, RL-Duet, ReaLchords, ASAP, MAESTRO |
|  41   | Благодарности                 |   |

Жирным выделены **новые блоки** по сравнению с предыдущей версией:
введение, выводы DTW/HMM, MDP-формализация, обоснование формулы
награды, литература.

## Соответствие фирменному стилю команды

- **Тема:** `Madrid` + `\usecolortheme{seahorse}` --- точно как в
  `HW_3_PRESENTATION.tex` и `HW_10_PRESENTATION_NP.tex`.
- **Кодировка:** `T2A` + `inputenc{utf8}` + `babel{russian}`.
- **Логотип:** ЦУ через `\logo{\includegraphics{cu_logo.png}}`.
- **Без `\pause`** --- ничего не появляется по щелчку.
- **Подсветка ключевых слов:** `\rlhi{...}` --- синий жирный
  (палитра seahorse).
- **Численные примеры** оформлены как в `HW_3_PRESENTATION.tex`
  (этап 1, этап 2, этап 3 SSMM): отдельные слайды с пошаговым
  выводом и конкретными числами.
- **Список литературы:** `\begin{thebibliography}` --- 3 слайда
  по тематикам.

## Соответствие тезисам

Слайды 26--29 воспроизводят буква-в-букву:

- **РИС. 1** из `article/тезисы.pdf` (схема архитектуры с
  $\pi_\theta$, средой, наградой);
- **Формула (1)** награды
  $r_t = -|t^{\text{render}}_t - t^{\text{perf}}_t| - \lambda L_{\text{align}}(t) - \mu (a_t - a_{t-1})^2$
  с теми же тремя `\underbrace`-объяснениями, что и в тезисах.

Дополнительно на слайдах 29--30 разобрано
\emph{почему именно такая формула}: $L_1$ вместо $L_2$ для
синхронизации (робастность к выбросам), KL-дивергенция как мягкая
регуляризация, $L_2$ для гладкости темпа.
