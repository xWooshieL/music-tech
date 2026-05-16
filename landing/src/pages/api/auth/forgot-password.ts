/**
 * POST /api/auth/forgot-password
 *
 * принимает { email }
 * - если пользователя нет — всё равно возвращаем ok (не палим existence)
 * - иначе генерируем токен, кладём в redis на 30 минут, шлём письмо со ссылкой
 *   <APP_URL>/reset-password?token=...
 */

import type { APIRoute } from "astro";
import {
  isValidEmail,
  k,
  makeToken32,
  normalizeEmail,
  rateLimit,
  redis,
  sendPasswordResetEmail,
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
  if (!isValidEmail(email)) {
    return json({ ok: false, error: "укажите корректный e-mail" }, 400);
  }

  // rate-limit: не более 3 раз в час на e-mail
  const limit = await rateLimit(`forgot:${email}`, 60 * 60, 3);
  if (!limit.ok) {
    return json({
      ok: true, // намеренно: не сообщаем что юзер существует
      message: "если такой e-mail зарегистрирован, ссылка отправлена",
    });
  }

  try {
    const r = redis();
    const user = await r.get(k.user(email));
    if (user) {
      const token = makeToken32();
      await r.set(k.resetToken(token), { email }, { ex: 60 * 30 });

      const appUrl =
        process.env.APP_URL ||
        new URL(request.url).origin;
      const link = `${appUrl}/reset-password?token=${encodeURIComponent(token)}`;

      await sendPasswordResetEmail(email, link);
    }

    // ответ одинаковый и для существующих и для несуществующих
    return json({
      ok: true,
      message: "если такой e-mail зарегистрирован, ссылка отправлена",
    });
  } catch (err: any) {
    console.error("forgot-password error:", err?.message ?? err);
    return json({ ok: false, error: "внутренняя ошибка, попробуйте позже" }, 500);
  }
};

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}
