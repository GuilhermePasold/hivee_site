import { chromium } from "playwright-core";
import { mkdirSync } from "node:fs";

const BASE = "http://localhost:5200";
const OUT = "c:/Users/guipa/Documents/HIVEE SITE/frontend/_shots";
mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch({ channel: "msedge", headless: true });
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
const page = await ctx.newPage();

await page.goto(BASE + "/", { waitUntil: "networkidle" });
await page.waitForTimeout(2500);
await page.screenshot({ path: `${OUT}/v-0.png` });
console.log("v-0");

for (const y of [1000, 1700, 2500, 3300, 4100, 4900]) {
  await page.evaluate((v) => window.scrollTo(0, v), y);
  await page.waitForTimeout(1000);
  await page.screenshot({ path: `${OUT}/v-${y}.png` });
  console.log("v", y);
}

await browser.close();
console.log("done");
