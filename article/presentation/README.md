# Презентация MusicTech — «Научный Телеграф» 2026

Доклад на 15–20 минут, **25 страниц** (титул + 6 outline-секций + 18
содержательных слайдов). Стиль — beamer-шаблон University of
Birmingham (`template/`), адаптированный под Центральный Университет:
тёмный фон, фирменный жёлтый акцент, шрифты Marcellus + Manrope
(включены в `template/fonts/`), логотип ЦУ в `template/logos/`.

## Структура папки

```
article/presentation/
├── presentation.tex          ← preamble + \input{sections/...}
├── presentation.pdf          ← собранный PDF (25 страниц, 16:9, ~600 КБ)
├── build.ps1                 ← два прогона xelatex
├── README.md
├── template/                 ← UoB beamer theme (адаптирован под ЦУ)
│   ├── beamerthemeuob.sty
│   ├── beamercolorthemeuob.sty
│   ├── beamerfontthemeuob.sty
│   ├── beamerinnerthemeuob.sty
│   ├── beamerouterthemeuob.sty
│   ├── fonts/
│   │   ├── Manrope.ttf       (с кириллицей, основной шрифт)
│   │   └── Marcellus.ttf     (только латиница, для лат.\ заголовков)
│   └── logos/
│       ├── UoB_dark.png      (логотип ЦУ для тёмной темы)
│       └── UoB_light.png     (логотип ЦУ для светлой темы)
├── sections/                 ← 17 .tex-фрагментов по слайдам 2-18
│   ├── 02-problem.tex
│   ├── ...
│   └── 18-thanks.tex
└── figures/
    ├── generate_plots.py     ← matplotlib-скрипт перегенерации графиков
    ├── png/                  ← 5 ручных схем из исходного шаблона
    │   ├── world_view.png        (Слайд 2 — солист vs оркестр)
    │   ├── system_pipeline.png   (Слайд 3 — pipeline)
    │   ├── oltw_dp.png           (Слайд 6 — OLTW DP)
    │   ├── hmm_chain.png         (Слайд 7 — HMM цепь состояний)
    │   └── hybrid_fusion.png     (Слайд 9 — Hybrid)
    ├── generated/            ← 5 ч/б PDF-графиков из реальных данных
    │   ├── rach_solo_pitch_time.pdf   (Слайд 4 — 3797 state Рахманинова)
    │   ├── rach_duration_hist.pdf
    │   ├── rubato_deviations.pdf      (Слайд 5)
    │   ├── oltw_trajectory.pdf        (Слайд 10)
    │   └── alpha_heatmap.pdf          (Слайд 10)
    └── tikz/                 ← 7 TikZ-схем для остальных слайдов
        ├── hsmm-duration.tex          (Слайд 8)
        ├── reactive-vs-anticip.tex    (Слайд 11)
        ├── proposed-arch.tex          (Слайд 12, РИС. 1 тезисов)
        ├── state-encoder.tex          (Слайд 14, sₜ ∈ ℝ¹⁸)
        ├── training-pipeline.tex      (Слайд 15, BC + PPO)
        ├── simulator-loop.tex         (Слайд 16, замкнутый цикл)
        └── roadmap-timeline.tex       (Слайд 17, план)
```

## Сборка

**Важно:** требуется **xelatex** (не pdflatex) — из-за `fontspec` и TTF.

```powershell
cd article/presentation
.\build.ps1
```

или вручную:

```powershell
xelatex -interaction=nonstopmode presentation.tex
xelatex -interaction=nonstopmode presentation.tex
```

Два прогона нужны для outline-слайдов между секциями. Результат —
`presentation.pdf`, 25 страниц, ≈ 0.6 МБ.

Если нужно **перегенерировать графики Рахманинова**:

```powershell
cd article/presentation/figures
python generate_plots.py
```

## Как устроена визуальная адаптация под тёмный фон

Все наши схемы (PNG, PDF, TikZ) нарисованы в чёрно-белом научном
стиле (белый фон, чёрные линии и текст) — это согласовано со
статьёй и тезисами. На тёмном фоне UoB-темы они бы стали
нечитаемыми, поэтому каждое изображение оборачивается в макрос
`\whitepane{...}` (определён в `presentation.tex`):

```latex
\newcommand{\whitepane}[1]{%
  \begingroup\setlength{\fboxsep}{4pt}%
  \colorbox{white}{\color{black}#1}%
  \endgroup}
```

`\whitepane` ставит белую плашку с отступами 4 pt вокруг
изображения. Получаем «галерейный» эффект: тёмный слайд, на нём
яркие белые карточки с научной графикой.

Жёлтые акценты (`\rlhi{...}`), цвет цитат (`\figcaption{...}`,
`lightyellow` italic) и фирменный жёлтый шрифт `Цель:` /
`не зависит от длины пьесы` подсвечивают **ключевую идею** доклада.

JSON-листинги оформлены через `lstlisting[style=darkjson]` —
жёлтая рамка, белый/жёлтый/голубой синтаксис на чёрной плашке.

## Что на каком слайде

(нумерация PDF, учитывает outline-слайды от `\section{}`)

| #  | Что                                          | Визуал                                   |
|----|----------------------------------------------|------------------------------------------|
| 1  | Титульник                                    | `template/logos/UoB_dark.png` (ЦУ)       |
| 2  | Outline: Постановка задачи и pipeline        | —                                        |
| 3  | Проблема                                     | `png/world_view.png`                     |
| 4  | Pipeline системы                             | `png/system_pipeline.png`                |
| 5  | Outline: Данные                              | —                                        |
| 6  | Формат партитуры (`score.json`)              | `generated/rach_solo_pitch_time.pdf`     |
| 7  | Performance MIDI / rubato                    | `generated/rubato_deviations.pdf`        |
| 8  | Outline: Классические трекеры                | —                                        |
| 9  | OLTW                                         | `png/oltw_dp.png`                        |
| 10 | HMM                                          | `png/hmm_chain.png`                      |
| 11 | HSMM                                         | `tikz/hsmm-duration.tex`                 |
| 12 | Hybrid Fusion                                | `png/hybrid_fusion.png`                  |
| 13 | Результаты baseline на синтетике             | `oltw_trajectory` + `alpha_heatmap`      |
| 14 | Outline: Гипотеза RL                         | —                                        |
| 15 | Почему baseline недостаточно                 | `tikz/reactive-vs-anticip.tex`           |
| 16 | Предлагаемая архитектура (РИС.\,1 тезисов)   | `tikz/proposed-arch.tex`                 |
| 17 | Математика RL-слоя: формулы                  | —                                        |
| 18 | Энкодер состояния $s_t$                      | `tikz/state-encoder.tex`                 |
| 19 | Outline: Обучение                            | —                                        |
| 20 | Обучение BC → PPO + KL                       | `tikz/training-pipeline.tex`             |
| 21 | Симулятор солиста и рендера                  | `tikz/simulator-loop.tex`                |
| 22 | Outline: Итоги                               | —                                        |
| 23 | Что готово и план                            | `tikz/roadmap-timeline.tex`              |
| 24 | Выводы                                       | —                                        |
| 25 | Спасибо / Вопросы                            | QR на репозиторий                        |

## Соответствие тезисам

Слайды 16–17 воспроизводят буква-в-букву:

- **РИС. 1** из `article/тезисы.pdf` (схема архитектуры с
  $\pi_\theta$, средой, наградой);
- **Формула (1)** награды
  $r_t = -|t^{\text{render}}_t - t^{\text{perf}}_t| - \lambda L_{\text{align}}(t) - \mu (a_t - a_{t-1})^2$
  с теми же тремя `\underbrace`-объяснениями.

## Шрифты и кириллица

- `Manrope.ttf` — sans-serif **с кириллицей** (Google Fonts). Это
  основной шрифт всего текста.
- `Marcellus.ttf` — serif **без кириллицы**. Используется в шаблоне
  как `\titlefont` для крупных заголовков, но `presentation.tex`
  явно переопределяет `\titlefont` на Manrope, иначе заголовки
  слайдов и `\inserttitle` пропадают.
- `DejaVu Sans Mono` (`\setmonofont`) — для `\texttt{...}`, нужен
  для корректного `\texttt{score.json}` и других русских блоков
  кода.

Шаблон поддерживает переключение тёмной/светлой темы:
`\usetheme[light]{uob}` — если кому-то покажется, что тёмный режим
слишком радикален для конкретного проектора.
