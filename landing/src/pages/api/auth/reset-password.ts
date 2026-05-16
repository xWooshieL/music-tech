/**
 * POST /api/auth/reset-password
 *
 * принимает { token, new_password }
 * - читает email из k.resetToken(token), удаляет токен сразу
 * - перезаписывает pwdHash у пользователя
 * - выдаёт новый jwt (опционально)
 */

import type { APIRoute } from "astro";
import {
  hashPassword,
  issueToken,
  k,
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

  const token       = String(body?.token        ?? "").trim();
  const newPassword = String(body?.new_password ?? "");

  if (!token) {
    return json({ ok: false, error: "ссылка некорректна" }, 400);
  }
  if (newPassword.length < 8) {
    return json({ ok: false, error: "новый пароль должен быть от 8 символов" }, 400);
  }

  try {
    const r = redis();
    const entry = (await r.get(k.resetToken(token))) as { email: string } | null;
    if (!entry) {
      return json({ ok: false, error: "ссылка устарела или уже использована" }, 410);
    }
    // одноразовое использование
    await r.del(k.resetToken(token));

    const email = entry.email;
    const user = (await r.get(k.user(email))) as
      | { email: string; name: string; pwdHash: string }
      | null;
    if (!user) {
      return json({ ok: false, error: "аккаунт не найден" }, 404);
    }

    const pwdHash = await hashPassword(newPassword);
    await r.set(k.user(email), { ...user, pwdHash });

    const jwt = await issueToken(email, user.name);
    return json({ ok: true, token: jwt, name: user.name }, 200, {
      "set-cookie": [
        `musictech_session=${jwt}`,
        "Path=/",
        "HttpOnly",
        "Secure",
        "SameSite=Lax",
        `Max-Age=${60 * 60 * 24 * 30}`,
      ].join("; "),
    });
  } catch (err: any) {
    console.error("reset-password error:", err?.message ?? err);
    return json({ ok: false, error: "внутренняя ошибка, попробуйте позже" }, 500);
  }
};

function json(data: unknown, status = 200, extra: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      ...extra,
    },
  });
}
