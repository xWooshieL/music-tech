// @ts-check
import { defineConfig } from "astro/config";
import tailwind from "@astrojs/tailwind";
import vercel from "@astrojs/vercel";

// деплоимся на Vercel: статика собирается в .vercel/output/static,
// API-эндпоинты упаковываются как serverless functions
export default defineConfig({
  site: process.env.APP_URL || "https://musictech.art",
  base: "/",

  output: "server",
  adapter: vercel({
    webAnalytics: { enabled: false },
    imageService: false,
    maxDuration: 10,
  }),

  trailingSlash: "ignore",
  integrations: [
    tailwind({
      applyBaseStyles: false,
    }),
  ],
});
