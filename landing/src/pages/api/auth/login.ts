/**
 * POST /api/auth/login
 *
 * принимает { email, password }
 * - читает user-запись
 * - проверяет пароль (scrypt)
 * - rate-limit 5 попыток в 10 минут на e-mail
 * - выдаёт jwt в теле и куки
 */

import type { APIRoute } from "astro";
import {
  buildSessionCookie,
  getUser,
  isValidEmail,
  issueToken,
  normalizeEmail,
  rateLimit,
  roleOf,
  verifyPassword,
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

  if (!isValidEmail(email) || !password) {
    return json({ ok: false, error: "укажите e-mail и пароль" }, 400);
  }

  try {
    const limit = await rateLimit(`login:${email}`, 60 * 10, 5);
    if (!limit.ok) {
      return json({
        ok: false,
        error: `слишком много попыток, подождите ${limit.resetIn}с`,
      }, 429);
    }

    const user = await getUser(email);
    if (!user) {
      return json({ ok: false, error: "неверный e-mail или пароль" }, 401);
    }

    const ok = await verifyPassword(password, user.pwdHash);
    if (!ok) {
      return json({ ok: false, error: "неверный e-mail или пароль" }, 401);
    }

    const token = await issueToken(email, user.name);
    return json({
      ok: true,
      token,
      user: {
        email:     user.email,
        name:      user.name,
        plan:      user.plan ?? "open-beta",
        role:      roleOf(user.email),
        createdAt: user.createdAt,
      },
    }, 200, sessionCookie(token));
  } catch (err: any) {
    console.error("login error:", err?.message ?? err);
    return json({ ok: false, error: "внутренняя ошибка, попробуйте позже" }, 500);
  }
};

function sessionCookie(token: string): Record<string, string> {
  return { "set-cookie": buildSessionCookie(token, 60 * 60 * 24 * 30) };
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
