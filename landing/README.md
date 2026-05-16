# MusicTech Landing — `musictech.art`

Лендинг с реальной авторизацией и восстановлением пароля.

## Стек

| Слой | Технология |
|---|---|
| Static + SSR | **Astro 5** в `output: "server"` |
| Стили | Tailwind CSS 3, scroll-reveal через IntersectionObserver |
| Хостинг | **Vercel** (serverless functions для API) |
| Email | **Resend** (3000 писем/мес бесплатно) |
| База данных | **Upstash Redis** (10000 команд/день бесплатно) |
| JWT | `jose` |
| Хеш паролей | `node:crypto.scrypt` |

## Структура

```
landing/
├── astro.config.mjs           ← @astrojs/vercel adapter, output: "server"
├── vercel.json
├── package.json
├── tailwind.config.mjs
├── .env.example               ← список переменных окружения
├── public/
└── src/
    ├── lib/
    │   └── auth.ts            ← redis, jwt, scrypt, resend клиенты + email-шаблоны
    ├── layouts/Base.astro
    ├── components/            ← Header / Hero / Features / HowItWorks / Download / FAQ / Footer
    └── pages/
        ├── index.astro
        ├── login.astro
        ├── register.astro     → POST /api/auth/register
        ├── verify.astro       → POST /api/auth/verify
        ├── forgot-password.astro → POST /api/auth/forgot-password
        ├── reset-password.astro  → POST /api/auth/reset-password
        ├── download.astro
        ├── about.astro
        ├── privacy.astro
        ├── terms.astro
        └── api/auth/
            ├── register.ts        ← валидация + redis + resend
            ├── verify.ts          ← код, попытки, jwt
            ├── login.ts           ← scrypt verify + jwt
            ├── forgot-password.ts ← одноразовый токен 30 мин
            └── reset-password.ts  ← смена пароля + новый jwt
```

## Flow

### Регистрация

```
[форма] POST /api/auth/register {email, password, name}
  ├── валидация
  ├── проверка что аккаунта ещё нет
  ├── rate-limit (1 в минуту, 5 в час на e-mail)
  ├── redis SET pending:<email> {name, pwdHash, code, attempts:0} EX 600
  └── resend.emails.send → письмо с 6-значным кодом

[форма /verify] POST /api/auth/verify {email, code}
  ├── читает pending:<email>
  ├── сверяет код (макс 5 неверных попыток)
  ├── создаёт user:<email>, удаляет pending
  └── выдаёт JWT (cookie + body) → редирект на /download
```

### Восстановление пароля

```
[форма /forgot-password] POST /api/auth/forgot-password {email}
  ├── ответ одинаков для существующих и несуществующих (не палим)
  ├── если юзер есть: token = random(24 bytes b64url)
  ├── redis SET reset:<token> {email} EX 1800
  └── resend → письмо со ссылкой /reset-password?token=...

[форма /reset-password] POST /api/auth/reset-password {token, new_password}
  ├── читает reset:<token>, удаляет (одноразово)
  ├── обновляет pwdHash у user:<email>
  └── выдаёт новый JWT
```

### Десктопное приложение

Mock-flow для будущей интеграции уже работает: после успешной регистрации/входа
браузер кладёт в `localStorage`:

```js
localStorage.getItem("musictech.token")   // jwt
localStorage.getItem("musictech.email")
localStorage.getItem("musictech.name")
```

Приложение откроет `https://musictech.art/login`, дождётся диплинка
`musictech://auth?token=<jwt>`, сохранит токен в системный keychain и
будет слать его в `Authorization: Bearer ...`.

## Запуск локально

```bash
cd landing
npm install
cp .env.example .env       # заполни значениями
npm run dev                # http://localhost:4321
```

Без заполненных `.env` API-эндпоинты вернут ошибку «env X is not set»;
фронт (статические страницы) откроется в любом случае.

## Деплой на Vercel

1. **Зарегистрируйся на Resend** → https://resend.com
   - создай API key (Dashboard → API Keys → Create);
   - в sandbox-режиме письма уходят только на e-mail, к которому привязан
     аккаунт resend — для теста этого достаточно;
   - когда подключишь домен `musictech.art` — добавь его в Resend → Domains,
     пропиши SPF/DKIM записи в DNS и поменяй `RESEND_FROM_EMAIL` на
     `noreply@musictech.art`.

2. **Зарегистрируйся на Upstash** → https://upstash.com
   - Create Database → eu-west или fra1 регион (рядом с Vercel);
   - в карточке БД скопируй `REST URL` и `REST Token`.

3. **Сгенерируй JWT secret:**

   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

4. **Создай проект Vercel:**
   - https://vercel.com/new → Import репозиторий `music-tech`;
   - Root Directory: `landing`;
   - Framework Preset: Astro (определится сам);
   - Environment Variables → добавь все из `.env.example`:

     ```
     RESEND_API_KEY=re_xxxxxxxxxxxxxxxxx
     RESEND_FROM_EMAIL=onboarding@resend.dev
     UPSTASH_REDIS_REST_URL=https://xxxx.upstash.io
     UPSTASH_REDIS_REST_TOKEN=xxxxxxxxxxxx
     JWT_SECRET=<длинная случайная строка>
     APP_URL=https://musictech-landing.vercel.app   # пока без своего домена
     ```

   - Deploy → через ~1 минуту сайт работает.

5. **Подключи домен `musictech.art`:**
   - в Vercel Project Settings → Domains → Add → `musictech.art`;
   - Vercel выдаст DNS-записи (A или CNAME), пропиши их у регистратора;
   - дождись verification (обычно 5–30 минут);
   - обнови `APP_URL=https://musictech.art` в Environment Variables;
   - в Resend → Domains → Add Domain → `musictech.art` → пропиши SPF/DKIM/DMARC;
   - после Verified обнови `RESEND_FROM_EMAIL=noreply@musictech.art`.

## Тестирование без покупки домена

Resend в sandbox-режиме шлёт письма **только на адрес, привязанный к
аккаунту resend.com**. То есть для теста:

1. Регистрируешься на resend.com через `your@mail.com`;
2. На лендинге регистрируешься тоже через `your@mail.com`;
3. Письмо реально придёт в твою почту;
4. Вводишь код, всё работает.

Если ввести **другой** e-mail в sandbox-режиме — Resend вернёт 422 и письмо
не уйдёт. После подключения своего домена `musictech.art` это ограничение
снимется.

## Бюджеты бесплатных tier-ов

| Сервис | Лимит | Когда упрёмся |
|---|---|---|
| **Resend** | 3000 писем/мес, 100/день | при ≥100 регистраций в день |
| **Upstash** | 10000 команд/день, 256 МБ | при ≥5000 регистраций в день |
| **Vercel** | 100 GB-ч functions, 100 GB трафика | при ≥1M запросов/мес |
| **JWT** | ∞ | никогда |

Для лендинга и MVP этого хватит с большим запасом.
