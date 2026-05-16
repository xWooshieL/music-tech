/**
 * POST /api/auth/verify
 *
 * принимает { email, code }
 * - читает pending-запись по e-mail
 * - проверяет код, считает неудачные попытки (макс 5)
 * - создаёт user-запись и выдаёт jwt-токен
 * - кладёт токен в cookie musictech_session и возвращает его в теле
 */

import type { APIRoute } from "astro";
import {
  isValidEmail,
  issueToken,
  k,
  normalizeEmail,
  rateLimit,
  redis,
} from "../../../lib/auth";

export const prerender = false;

export const POST: APIRoute = async ({ request }) => {
  let body: any;
  try {
    body = await request.json();
  } catch {
    return json({ ok: false, error: "invalid json" }, 400);
  }

  const email = normalizeEmail(String(body?.email ?? ""));
  const code  = String(body?.code ?? "").trim();

  if (!isValidEmail(email)) {
    return json({ ok: false, error: "укажите корректный e-mail" }, 400);
  }
  if (!/^\d{6}$/.test(code)) {
    return json({ ok: false, error: "код должен состоять из 6 цифр" }, 400);
  }

  try {
    const r = redis();
    const limit = await rateLimit(`ver:${email}`, 60, 10);
    if (!limit.ok) {
      return json({
        ok: false,
        error: `слишком частые попытки, подождите ${limit.resetIn}с`,
      }, 429);
    }

    const pending = (await r.get(k.pending(email))) as
      | { name: string; pwdHash: string; code: string; attempts: number }
      | null;

    if (!pending) {
      return json({
        ok: false,
        error: "код устарел или регистрация не начата",
      }, 410);
    }

    if (pending.attempts >= 5) {
      await r.del(k.pending(email));
      return json({
        ok: false,
        error: "слишком много неверных попыток, начните регистрацию заново",
      }, 429);
    }

    if (pending.code !== code) {
      await r.set(
        k.pending(email),
        { ...pending, attempts: pending.attempts + 1 },
        { keepTtl: true },
      );
      return json({
        ok: false,
        error: "неверный код",
        attempts_left: 5 - (pending.attempts + 1),
      }, 401);
    }

    // успех: создаём пользователя, удаляем pending
    await r.set(k.user(email), {
      email,
      name: pending.name,
      pwdHash: pending.pwdHash,
      createdAt: Date.now(),
    });
    await r.del(k.pending(email));

    const token = await issueToken(email, pending.name);
    return json({ ok: true, token, name: pending.name }, 200, sessionCookie(token));
  } catch (err: any) {
    console.error("verify error:", err?.message ?? err);
    return json({ ok: false, error: "внутренняя ошибка, попробуйте позже" }, 500);
  }
};

function sessionCookie(token: string): Record<string, string> {
  const cookie = [
    `musictech_session=${token}`,
    "Path=/",
    "HttpOnly",
    "Secure",
    "SameSite=Lax",
    `Max-Age=${60 * 60 * 24 * 30}`,
  ].join("; ");
  return { "set-cookie": cookie };
}

function json(data: unknown, status = 200, extra: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      ...extra,
    },
  });
}
