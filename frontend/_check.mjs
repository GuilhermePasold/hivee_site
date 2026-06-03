import { chromium } from "playwright-core";

const BASE = "http://localhost:5200";
const OUT = "c:/Users/guipa/Documents/HIVEE SITE/frontend/_shots";

const browser = await chromium.launch({ channel: "msedge", headless: true });
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
const page = await ctx.newPage();

const errors = [];
page.on("console", (m) => { if (m.type() === "error") errors.push("CONSOLE: " + m.text()); });
page.on("pageerror", (e) => errors.push("PAGEERROR: " + e.message));

await page.goto(BASE + "/", { waitUntil: "networkidle" });
await page.waitForTimeout(3000);
await page.screenshot({ path: `${OUT}/chk-intro.png` });

// scroll partway through cinematic
await page.evaluate(() => window.scrollTo(0, 500)); await page.waitForTimeout(1200);
await page.screenshot({ path: `${OUT}/chk-mid.png` });
await page.evaluate(() => window.scrollTo(0, 1200)); await page.waitForTimeout(1200);
await page.screenshot({ path: `${OUT}/chk-after.png` });

console.log("ERRORS:", errors.length);
errors.slice(0, 20).forEach((e) => console.log(e));
await browser.close();
