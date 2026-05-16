/**
 * POST /api/auth/register
 *
 * принимает { email, password, name }
 * - валидирует e-mail и длину пароля
 * - проверяет что аккаунт ещё не создан
 * - сохраняет pending-запись в redis с 6-значным кодом на 10 минут
 * - отправляет код на e-mail через resend
 * - rate-limit: 1 код в минуту на e-mail, 5 в час суммарно
 */

import type { APIRoute } from "astro";
import {
  hashPassword,
  isValidEmail,
  k,
  makeCode,
  normalizeEmail,
  rateLimit,
  redis,
  sendVerificationCode,
} from "../../../lib/auth";

export const prerender = false;

export const POST: APIRoute = async ({ request }) => {
  let body: any;
  try {
    body = await request.json();
  } catch {
    return json({ ok: false, error: "invalid json" }, 400);
  }

  const email    = normalizeEmail(String(body?.email    ?? ""));
  const password = String(body?.password ?? "");
  const name     = String(body?.name     ?? "").trim();

  if (!isValidEmail(email)) {
    return json({ ok: false, error: "укажите корректный e-mail" }, 400);
  }
  if (password.length < 8) {
    return json({ ok: false, error: "пароль должен быть от 8 символов" }, 400);
  }
  if (name.length < 2 || name.length > 60) {
    return json({ ok: false, error: "имя от 2 до 60 символов" }, 400);
  }

  try {
    const r = redis();

    // аккаунт уже существует?
    const exists = await r.exists(k.user(email));
    if (exists) {
      return json(
        { ok: false, error: "аккаунт с таким e-mail уже существует" },
        409,
      );
    }

    // rate-limit
    const perMinute = await rateLimit(`reg:${email}:1m`,    60,   1);
    if (!perMinute.ok) {
      return json({
        ok: false,
        error: `подождите ${perMinute.resetIn}с до следующей попытки`,
      }, 429);
    }
    const perHour = await rateLimit(`reg:${email}:1h`, 60 * 60,   5);
    if (!perHour.ok) {
      return json({
        ok: false,
        error: "слишком много попыток, попробуйте через час",
      }, 429);
    }

    const code = makeCode();
    const pwdHash = await hashPassword(password);

    await r.set(
      k.pending(email),
      { name, pwdHash, code, attempts: 0 },
      { ex: 60 * 10 },
    );

    await sendVerificationCode(email, code);

    return json({
      ok: true,
      message: "код отправлен на e-mail",
      expires_in: 600,
    });
  } catch (err: any) {
    console.error("register error:", err?.message ?? err);
    return json({ ok: false, error: "не удалось отправить код, попробуйте позже" }, 500);
  }
};

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}
