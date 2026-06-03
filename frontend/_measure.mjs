import { chromium } from "playwright-core";

const browser = await chromium.launch({ channel: "msedge", headless: true });
const page = await browser.newContext({ viewport: { width: 1440, height: 900 } }).then((c) => c.newPage());
await page.goto("http://localhost:5200/", { waitUntil: "networkidle" });
await page.waitForTimeout(2500);

const info = await page.evaluate(() => {
  const out = [];
  out.push("bodyScrollHeight=" + document.body.scrollHeight);
  const home = document.querySelector("main > div");
  if (home) {
    [...home.children].forEach((c, i) => {
      const r = c.getBoundingClientRect();
      out.push(`child[${i}] <${c.tagName}.${(c.className || "").toString().slice(0, 40)}> offsetTop=${Math.round(c.offsetTop)} h=${Math.round(c.offsetHeight)}`);
    });
  }
  // minimalist hero (2nd child) internal
  const hero = home?.children[1];
  if (hero) {
    out.push("---- hero internals ----");
    [...hero.children].forEach((c, i) => {
      out.push(`hero[${i}] <${c.tagName}> h=${Math.round(c.offsetHeight)}`);
    });
  }
  return out;
});
console.log(info.join("\n"));
await browser.close();
