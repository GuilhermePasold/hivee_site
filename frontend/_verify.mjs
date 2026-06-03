import { chromium } from "playwright-core";
const OUT = "c:/Users/guipa/Documents/HIVEE SITE/frontend/_shots";
const browser = await chromium.launch({ channel: "msedge", headless: true });
const page = await browser.newContext({ viewport: { width: 1440, height: 900 } }).then((c) => c.newPage());

await page.goto("http://localhost:5200/buscar", { waitUntil: "networkidle" });
await page.waitForTimeout(2500);
// open the city dropdown to confirm it's not clipped/behind cards
await page.locator("text=Todas as cidades").first().click().catch(() => {});
await page.waitForTimeout(700);
await page.screenshot({ path: `${OUT}/vf-buscar-dropdown.png` });
console.log("buscar dropdown");

await page.goto("http://localhost:5200/minha-conta", { waitUntil: "networkidle" });
await page.waitForTimeout(1500);
await page.screenshot({ path: `${OUT}/vf-conta.png` });
console.log("conta");

await browser.close();
