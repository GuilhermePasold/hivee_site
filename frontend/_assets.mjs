import { chromium } from "playwright-core";

const BASE = "http://localhost:5200";
const PUB = "c:/Users/guipa/Documents/HIVEE SITE/frontend/public";

const browser = await chromium.launch({ channel: "msedge", headless: true });
const ctx = await browser.newContext({
  viewport: { width: 402, height: 874 },
  deviceScaleFactor: 2,
});
const page = await ctx.newPage();

// Grab a real provider slug from the API.
let slug = "";
try {
  await page.goto(`${BASE}/api/providers/?page_size=1`, { waitUntil: "networkidle" });
  const txt = await page.evaluate(() => document.body.innerText);
  slug = JSON.parse(txt).results[0].slug;
} catch (e) {
  console.log("slug fetch failed", e.message);
}

await page.goto(`${BASE}/buscar`, { waitUntil: "networkidle" });
await page.waitForTimeout(2800);
await page.screenshot({ path: `${PUB}/shot-busca.png` });
console.log("shot-busca.png");

if (slug) {
  await page.goto(`${BASE}/prestador/${slug}`, { waitUntil: "networkidle" });
  await page.waitForTimeout(2800);
  await page.screenshot({ path: `${PUB}/shot-perfil.png` });
  console.log("shot-perfil.png", slug);
}

await browser.close();
console.log("assets done");
