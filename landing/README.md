# MusicTech Landing — `musictech.art`

Лендинг для проекта MusicTech. Сделан на Astro 5 + Tailwind CSS,
плавные анимации через scroll-reveal (IntersectionObserver, без
тяжёлых JS-библиотек), полностью статический.

## Что внутри

```
landing/
├── astro.config.mjs          ← конфиг + переключение base для gh-pages
├── tailwind.config.mjs
├── package.json
├── public/
│   └── favicon.svg
└── src/
    ├── layouts/Base.astro    ← общий шаблон, header + footer + scroll-reveal
    ├── components/           ← Hero, Features, HowItWorks, Download, FAQ, ...
    ├── pages/
    │   ├── index.astro       ← главный лендинг
    │   ├── login.astro       ← форма входа (mock auth в localStorage)
    │   ├── register.astro    ← регистрация
    │   ├── download.astro    ← скачивание установщика
    │   ├── about.astro       ← о команде
    │   ├── privacy.astro     ← политика конфиденциальности
    │   └── terms.astro       ← условия использования
    └── styles/global.css     ← Tailwind + кастомные компоненты
```

## Локальная разработка

```bash
cd landing
npm install
npm run dev          # http://localhost:4321
```

## Сборка

```bash
npm run build        # → landing/dist/
npm run preview      # превью собранного
```

## Деплой

Включён GitHub Action [`deploy-landing.yml`](../.github/workflows/deploy-landing.yml).
При push в `master` action собирает Astro и публикует `dist/` на
`gh-pages`.

После деплоя сайт открывается по адресу:

> **<https://nizier193.github.io/music-tech/>**

Когда настроим домен — пропишем в Cloudflare DNS `CNAME musictech.art
nizier193.github.io` и в репозитории добавим `landing/public/CNAME`.

## Интеграция с десктопным приложением

В будущем приложение MusicTech (Electron / native) откроет диплинк
вида `musictech://auth?token=<jwt>`. Сейчас веб-форма входа
сохраняет mock-токен в `localStorage`:

```javascript
localStorage.getItem("musictech.token")  // "musictech.<email-b64>.<ts-b64>"
localStorage.getItem("musictech.email")
```

Десктопное приложение сможет:

1. Открыть `https://musictech.art/login` в системном браузере.
2. Дождаться диплинка `musictech://auth?token=...`.
3. Сохранить токен в keychain ОС.
4. Каждый запрос к будущему API серверу слать с `Authorization: Bearer <token>`.

Сейчас сервера ещё нет — это план следующего спринта (FastAPI + JWT).

## Стек

- **Astro 5** — статический генератор, zero-JS по умолчанию.
- **Tailwind CSS 3** — стилизация без лишнего CSS-кода.
- **IntersectionObserver** — scroll-reveal без сторонних библиотек
  (anime.js, motion и GSAP при желании можно подключить, но базово
  не нужны).
- **`@fontsource-variable/inter`** — Inter Variable как локальный шрифт.

## Юридическое

- `privacy.astro` — политика конфиденциальности (ФЗ-152).
- `terms.astro` — условия использования.
- Открытый код ядра — MIT, см. репозиторий
  <https://github.com/Nizier193/music-tech>.
