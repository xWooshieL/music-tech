/**
 * общие auth-хелперы: хеш паролей, jwt, redis-клиент, отправка email
 *
 * единственное место где встречаются переменные окружения:
 *   RESEND_API_KEY            ключ resend.com для отправки писем
 *   RESEND_FROM_EMAIL         from-адрес (например no-reply@musictech.art)
 *   UPSTASH_REDIS_REST_URL    хранилище кодов и аккаунтов
 *   UPSTASH_REDIS_REST_TOKEN
 *   JWT_SECRET                любая длинная строка для подписи токенов
 *   APP_URL                   корень сайта, попадает в ссылки reset-password
 */

import { Redis } from "@upstash/redis";
import { SignJWT, jwtVerify } from "jose";
import { Resend } from "resend";
import { randomBytes, scrypt, timingSafeEqual } from "node:crypto";
import { promisify } from "node:util";

const scryptAsync = promisify(scrypt);

const env = {
  RESEND_API_KEY:            getenv("RESEND_API_KEY"),
  RESEND_FROM_EMAIL:         getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev"),
  UPSTASH_REDIS_REST_URL:    getenv("UPSTASH_REDIS_REST_URL"),
  UPSTASH_REDIS_REST_TOKEN:  getenv("UPSTASH_REDIS_REST_TOKEN"),
  JWT_SECRET:                getenv("JWT_SECRET"),
  APP_URL:                   getenv("APP_URL", "https://musictech.art"),
};

function getenv(key: string, fallback?: string): string {
  const v = process.env[key];
  if (v && v.length > 0) return v;
  if (fallback !== undefined) return fallback;
  // лениво проверяем — не падаем при импорте модуля, падаем при первом вызове
  return "";
}

function requireEnv(key: keyof typeof env): string {
  const v = env[key];
  if (!v) {
    throw new Error(
      `env ${key} is not set. добавь переменную окружения в vercel project settings`,
    );
  }
  return v;
}

// ---------------------------------------------------------------------------
// redis
// ---------------------------------------------------------------------------

let _redis: Redis | null = null;
export function redis(): Redis {
  if (_redis) return _redis;
  _redis = new Redis({
    url:   requireEnv("UPSTASH_REDIS_REST_URL"),
    token: requireEnv("UPSTASH_REDIS_REST_TOKEN"),
  });
  return _redis;
}

// ---------------------------------------------------------------------------
// password hashing (scrypt, без внешних зависимостей)
// ---------------------------------------------------------------------------

export async function hashPassword(password: string): Promise<string> {
  const salt = randomBytes(16);
  const key = (await scryptAsync(password, salt, 64)) as Buffer;
  return `scrypt$${salt.toString("hex")}$${key.toString("hex")}`;
}

export async function verifyPassword(
  password: string,
  stored: string,
): Promise<boolean> {
  const [alg, saltHex, keyHex] = stored.split("$");
  if (alg !== "scrypt" || !saltHex || !keyHex) return false;
  const salt = Buffer.from(saltHex, "hex");
  const expected = Buffer.from(keyHex, "hex");
  const actual = (await scryptAsync(password, salt, expected.length)) as Buffer;
  if (actual.length !== expected.length) return false;
  return timingSafeEqual(actual, expected);
}

// ---------------------------------------------------------------------------
// jwt
// ---------------------------------------------------------------------------

export interface SessionPayload {
  sub:   string;   // email
  name?: string;
  iat:   number;
  exp:   number;
}

const ISSUER = "musictech.art";
const AUDIENCE = "musictech-app";

function jwtKey(): Uint8Array {
  return new TextEncoder().encode(requireEnv("JWT_SECRET"));
}

export async function issueToken(
  email: string,
  name?: string,
  ttlSeconds = 60 * 60 * 24 * 30,
): Promise<string> {
  return await new SignJWT({ name })
    .setProtectedHeader({ alg: "HS256" })
    .setIssuedAt()
    .setSubject(email)
    .setIssuer(ISSUER)
    .setAudience(AUDIENCE)
    .setExpirationTime(`${ttlSeconds}s`)
    .sign(jwtKey());
}

export async function verifyToken(token: string): Promise<SessionPayload | null> {
  try {
    const { payload } = await jwtVerify(token, jwtKey(), {
      issuer:   ISSUER,
      audience: AUDIENCE,
    });
    return payload as unknown as SessionPayload;
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// email через resend
// ---------------------------------------------------------------------------

let _resend: Resend | null = null;
function resendClient(): Resend {
  if (_resend) return _resend;
  _resend = new Resend(requireEnv("RESEND_API_KEY"));
  return _resend;
}

export async function sendVerificationCode(
  to: string,
  code: string,
): Promise<void> {
  await resendClient().emails.send({
    from:    env.RESEND_FROM_EMAIL || "onboarding@resend.dev",
    to:      [to],
    subject: `MusicTech — код подтверждения ${code}`,
    text:
      `Ваш код подтверждения для MusicTech: ${code}\n\n` +
      `Код действует 10 минут. Если вы не регистрировались — просто игнорируйте письмо.\n\n` +
      `— Команда MusicTech\n${env.APP_URL}`,
    html: codeEmailHtml({
      title:   "Подтвердите регистрацию",
      hint:    "Введите этот код на странице подтверждения, чтобы завершить создание аккаунта.",
      code,
      footnote:
        "Если вы не регистрировались на musictech.art — просто игнорируйте это письмо.",
    }),
  });
}

export async function sendPasswordResetEmail(
  to: string,
  link: string,
): Promise<void> {
  await resendClient().emails.send({
    from:    env.RESEND_FROM_EMAIL || "onboarding@resend.dev",
    to:      [to],
    subject: "MusicTech — восстановление пароля",
    text:
      `Чтобы задать новый пароль, перейдите по ссылке (действует 30 минут):\n\n${link}\n\n` +
      `Если вы не запрашивали восстановление — игнорируйте это письмо.\n\n` +
      `— Команда MusicTech`,
    html: linkEmailHtml({
      title:   "Восстановление пароля",
      hint:    "Нажмите кнопку, чтобы задать новый пароль. Ссылка действует 30 минут.",
      buttonLabel: "Задать новый пароль",
      url:     link,
      footnote:
        "Если вы не запрашивали восстановление — игнорируйте это письмо. Ваш пароль не изменится.",
    }),
  });
}

// ---------------------------------------------------------------------------
// email templates — минимальный inline html, чтобы не зависеть от React Email
// ---------------------------------------------------------------------------

function shell(inner: string): string {
  return `<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:32px 16px;background:#f4f6f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#0f172a;">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
<tr><td align="center">
<table role="presentation" width="520" cellspacing="0" cellpadding="0" border="0"
       style="max-width:520px;background:#ffffff;border:1px solid #e2e8f0;border-radius:16px;overflow:hidden;">
<tr><td style="padding:28px 32px 0 32px;">
  <div style="display:flex;align-items:center;gap:8px;">
    <div style="width:28px;height:28px;border-radius:8px;background:linear-gradient(135deg,#34d399,#059669);display:inline-block;"></div>
    <span style="font-weight:700;font-size:18px;letter-spacing:-0.01em;">MusicTech</span>
  </div>
</td></tr>
${inner}
<tr><td style="padding:24px 32px 32px 32px;border-top:1px solid #e2e8f0;color:#64748b;font-size:12px;">
  Команда MusicTech · Центральный Университет (Т-Банк)<br>
  <a href="${escapeHtml(env.APP_URL)}" style="color:#059669;text-decoration:none;">${escapeHtml(env.APP_URL)}</a>
</td></tr>
</table>
</td></tr></table>
</body></html>`;
}

function codeEmailHtml(props: {
  title: string;
  hint: string;
  code: string;
  footnote: string;
}): string {
  return shell(`
<tr><td style="padding:24px 32px 8px 32px;">
  <h1 style="margin:0 0 12px 0;font-size:22px;letter-spacing:-0.01em;">${escapeHtml(props.title)}</h1>
  <p style="margin:0;color:#475569;font-size:14px;line-height:1.55;">${escapeHtml(props.hint)}</p>
</td></tr>
<tr><td style="padding:24px 32px;">
  <div style="text-align:center;padding:20px;background:#ecfdf5;border:1px solid #a7f3d0;border-radius:12px;">
    <div style="font-family:ui-monospace,Menlo,Monaco,Consolas,monospace;font-size:32px;letter-spacing:0.4em;font-weight:700;color:#065f46;">
      ${escapeHtml(props.code)}
    </div>
    <div style="margin-top:8px;font-size:12px;color:#047857;">код действует 10 минут</div>
  </div>
</td></tr>
<tr><td style="padding:0 32px 24px 32px;color:#64748b;font-size:12px;line-height:1.5;">
  ${escapeHtml(props.footnote)}
</td></tr>`);
}

function linkEmailHtml(props: {
  title: string;
  hint: string;
  buttonLabel: string;
  url: string;
  footnote: string;
}): string {
  return shell(`
<tr><td style="padding:24px 32px 8px 32px;">
  <h1 style="margin:0 0 12px 0;font-size:22px;letter-spacing:-0.01em;">${escapeHtml(props.title)}</h1>
  <p style="margin:0;color:#475569;font-size:14px;line-height:1.55;">${escapeHtml(props.hint)}</p>
</td></tr>
<tr><td style="padding:24px 32px;" align="center">
  <a href="${escapeHtml(props.url)}"
     style="display:inline-block;padding:14px 28px;background:#10b981;color:#ffffff;
            text-decoration:none;font-weight:600;border-radius:12px;font-size:14px;">
    ${escapeHtml(props.buttonLabel)}
  </a>
  <div style="margin-top:12px;font-size:12px;color:#64748b;">
    или скопируйте ссылку:<br>
    <a href="${escapeHtml(props.url)}" style="color:#059669;word-break:break-all;">${escapeHtml(props.url)}</a>
  </div>
</td></tr>
<tr><td style="padding:0 32px 24px 32px;color:#64748b;font-size:12px;line-height:1.5;">
  ${escapeHtml(props.footnote)}
</td></tr>`);
}

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

// ---------------------------------------------------------------------------
// rate-limit: не больше 1 кода в минуту на email и не больше 5 в час
// ---------------------------------------------------------------------------

export async function rateLimit(
  keyPrefix: string,
  ttlSeconds: number,
  limit: number,
): Promise<{ ok: boolean; resetIn: number }> {
  const key = `rl:${keyPrefix}`;
  const r = redis();
  const count = await r.incr(key);
  if (count === 1) await r.expire(key, ttlSeconds);
  if (count > limit) {
    const left = await r.ttl(key);
    return { ok: false, resetIn: Math.max(left, 1) };
  }
  return { ok: true, resetIn: 0 };
}

// ---------------------------------------------------------------------------
// helpers
// ---------------------------------------------------------------------------

export function makeCode(): string {
  // 6 цифр, без 0 в первой позиции
  const n = 100000 + Math.floor(Math.random() * 900000);
  return String(n);
}

export function makeToken32(): string {
  return randomBytes(24).toString("base64url");
}

export function normalizeEmail(email: string): string {
  return email.trim().toLowerCase();
}

export function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email);
}

// ---------------------------------------------------------------------------
// redis keys
// ---------------------------------------------------------------------------

export const k = {
  user:        (email: string) => `user:${email}`,
  pending:     (email: string) => `pending:${email}`,
  resetToken:  (token: string) => `reset:${token}`,
};
