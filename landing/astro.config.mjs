// @ts-check
import { defineConfig } from "astro/config";
import tailwind from "@astrojs/tailwind";

const isPages = process.env.DEPLOY_TARGET === "gh-pages";

export default defineConfig({
  // если деплоим на github pages — путь до подпапки /music-tech/
  site: isPages ? "https://nizier193.github.io" : "https://musictech.art",
  base: isPages ? "/music-tech" : "/",
  output: "static",
  trailingSlash: "ignore",
  integrations: [
    tailwind({
      applyBaseStyles: false,
    }),
  ],
});
