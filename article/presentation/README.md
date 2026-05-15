# Презентация MusicTech — «Научный Телеграф» 2026

Доклад на 15–20 минут, **19 слайдов**. Стиль согласован со статьёй
(`article/main.tex`) и тезисами (`article/тезисы.tex`): чёрно-белая
научная типографика, Times-подобный serif, минималистичный beamer
без украшений.

## Структура папки

```
article/presentation/
├── presentation.tex          ← preamble + \input{sections/...}
├── presentation.pdf          ← собранный PDF (19 страниц, 16:9)
├── build.ps1                 ← два прогона pdflatex
├── README.md
├── sections/                 ← 18 .tex-фрагментов, по одному на слайд
│   ├── 01-title.tex
│   ├── ...
│   └── 18-thanks.tex
└── figures/
    ├── generate_plots.py     ← matplotlib-скрипт перегенерации графиков
    ├── png/                  ← 5 ручных схем из шаблона презентации
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

```powershell
cd article/presentation
.\build.ps1
```

или вручную:

```powershell
pdflatex -interaction=nonstopmode presentation.tex
pdflatex -interaction=nonstopmode presentation.tex
```

Результат — `presentation.pdf` (19 страниц, ≈ 0.9 МБ).

Если нужно **перегенерировать графики Рахманинова** (например после
смены `rach_solo.json`):

```powershell
cd article/presentation/figures
python generate_plots.py
```

Скрипт читает реальные `rach_solo.json` (3797 state) и сохраняет
PDF/PNG в `generated/`.

## Что на каком слайде

| #  | Слайд                                | Визуал                                   |
|----|--------------------------------------|------------------------------------------|
| 1  | Титульник                            | —                                        |
| 2  | Проблема                             | `png/world_view.png`                     |
| 3  | Pipeline системы                     | `png/system_pipeline.png`                |
| 4  | Формат партитуры (`score.json`)      | `generated/rach_solo_pitch_time.pdf`     |
| 5  | Performance MIDI / rubato            | `generated/rubato_deviations.pdf`        |
| 6  | OLTW (baseline 1)                    | `png/oltw_dp.png`                        |
| 7  | HMM (baseline 2)                     | `png/hmm_chain.png`                      |
| 8  | HSMM (baseline 3)                    | `tikz/hsmm-duration.tex`                 |
| 9  | Hybrid Fusion (baseline 4)           | `png/hybrid_fusion.png`                  |
| 10 | Результаты baseline на синтетике     | `oltw_trajectory.pdf` + `alpha_heatmap.pdf` |
| 11 | Почему baseline недостаточно         | `tikz/reactive-vs-anticip.tex`           |
| 12 | Предлагаемая архитектура (РИС.\,1)   | `tikz/proposed-arch.tex`                 |
| 13 | Математика RL-слоя: формулы          | — (формулы)                              |
| 14 | Энкодер состояния $s_t$              | `tikz/state-encoder.tex`                 |
| 15 | Обучение BC → PPO + KL               | `tikz/training-pipeline.tex`             |
| 16 | Симулятор солиста и рендера          | `tikz/simulator-loop.tex`                |
| 17 | Что готово и план                    | `tikz/roadmap-timeline.tex`              |
| 18 | Выводы                               | —                                        |
| 19 | Спасибо / Вопросы                    | QR на репозиторий                        |

## Стиль графики

- Все растровые схемы (`png/`) — ручные draw.io диаграммы пользователя:
  чёрный контур, белая заливка, аккуратные стрелки, Times-подобный
  шрифт. Это «шаблон презентации».
- Графики (`generated/`) — matplotlib в чёрно-белом научном стиле
  (`grayscale`, `font.family=serif`, dotted grid). Шрифт совпадает
  со статьёй.
- TikZ-схемы (`tikz/`) — там, где нужна тонкая интеграция с формулами
  и счётчиками beamer. Сжимаются через `\resizebox{\linewidth}{!}{...}`
  чтобы вписаться в ширину колонки и не пересекаться с текстом.

## Соответствие тезисам

Слайды 12–13 воспроизводят буква-в-букву:

- **РИС. 1** из `article/тезисы.pdf` — схема архитектуры с
  $\pi_\theta$, средой, наградой;
- **Формула (1)** награды
  $r_t = -|t^{\text{render}}_t - t^{\text{perf}}_t| - \lambda L_{\text{align}}(t) - \mu (a_t - a_{t-1})^2$
  с теми же тремя `\underbrace`-объяснениями, что и в тезисах.

Это критично: внешний экспертный совет конференции будет сверять
презентацию с тезисами.

## Источник графика Рахманинова

Слайд 4 использует график pitch vs time, аналогичный ячейке 9 из
`src/musictech-app/notebooks/02_score_format.ipynb`. Те же данные
(`midi/rach_solo.json`, 3797 state, top-нота каждого аккорда),
переотрисованные в ч/б стиле для печатной презентации (см.
`figures/generate_plots.py::plot_rach_solo_pitch_time`).
