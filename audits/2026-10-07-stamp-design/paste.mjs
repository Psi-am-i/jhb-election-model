import fs from "node:fs";
const D = "/Users/simondavis/projects/atlas-jhb-election-model/audits/2026-10-07-stamp-design/";
const O = D + "owner-stamps/", M = "/Users/simondavis/.claude/jobs/26965cd4/tmp/mock/";
const F = (fam, file, w = "normal") => `@font-face{font-family:'${fam}';src:url(data:font/ttf;base64,${fs.readFileSync(O + "fonts/" + file).toString("base64")});font-weight:${w}}`;
const css = [F("BowlbyOne-Regular","BowlbyOne-Regular.ttf"),F("Bowlby One","BowlbyOne-Regular.ttf"),F("BerkshireSwash-Regular","BerkshireSwash-Regular.ttf"),F("Berkshire Swash","BerkshireSwash-Regular.ttf"),
  F("Aclonica-Regular","Aclonica-Regular.ttf"),F("LuckiestGuy-Regular","LuckiestGuy-Regular.ttf"),F("Lalezar-Regular","Lalezar-Regular.ttf"),F("Lalezar","Lalezar-Regular.ttf"),
  F("InstrumentSans-Bold","InstrumentSans-var.ttf","100 900"),F("InstrumentSans-Medium","InstrumentSans-var.ttf","100 900"),F("InstrumentSans-Regular","InstrumentSans-var.ttf","100 900"),F("Instrument Sans","InstrumentSans-var.ttf","100 900"),
  `@font-face{font-family:'Plex';src:url(data:font/woff2;base64,${fs.readFileSync("src/fonts/" + fs.readdirSync("src/fonts").find(f => /Sans-Regular/.test(f))).toString("base64")})}`].join("");
let uid = 0;
const stampSVG = (name, size) => {
  let s = fs.readFileSync(O + name + ".svg", "utf8").replace(/^[\s\S]*?(<svg)/, "$1").replace('width="100%" height="100%"', `width="${size}" height="${size * 637 / 688}"`);
  const p = "u" + (uid++) + "_";
  return s.replace(/id="([^"]+)"/g, `id="${p}$1"`).replace(/(href|xlink:href)="#([^"]+)"/g, `$1="#${p}$2"`).replace(/url\(#([^)]+)\)/g, `url(#${p}$1)`);
};
const img = f => "data:image/png;base64," + fs.readFileSync(M + f).toString("base64");
const K = "#141715";
const cards = [
  ["our-link", "m-colour-link.png", 1200, 630, [[0,0,1200,112,K],[40,120,530,52,K],[452,526,110,40,K],[40,566,530,30,K]], "official_forecast", 175, 128, 330,
    [["Johannesburg council<br>4 November 2026 · 270 seats<br>Made 7 October 2026",345,30,19,"#b6bcb6",400,240],["Our call: every ward, every seat.",48,568,17,"#868d86",400,520]]],
  ["reader-link", "share-card-link.png", 1200, 630, [[930,0,270,108,null],[452,528,100,34,K]], "long_shot", 1045, 150, 360, []],
  ["our-story", "m-colour-story.png", 1080, 1920, [[0,0,1080,292,K],[50,295,1000,80,K],[640,1410,200,60,K]], "official_forecast", 250, 200, 440,
    [["Johannesburg council<br>4 November 2026 · 270 seats<br>Made 7 October 2026<br>28 days to the vote",540,70,30,"#b6bcb6",400,500],["Our call: every ward, every seat.",540,250,26,"#868d86",400,500]]],
];
const body = cards.map(([id, base, W, H, covers, st, cx, cy, sz, texts]) => {
  const sh = sz * 637 / 688;
  return `<div id="${id}" style="position:relative;width:${W}px;height:${H}px;overflow:hidden">
    <img src="${img(base)}" style="position:absolute;left:0;top:0">
    ${covers.map(([x,y,w,h,c]) => `<div style="position:absolute;left:${x}px;top:${y}px;width:${w}px;height:${h}px;background:${c || "var(--band)"}" class="cv"></div>`).join("")}
    ${texts.map(([t,x,y,s,c,wt,mw]) => `<div style="position:absolute;left:${x}px;top:${y}px;max-width:${mw}px;font:${wt} ${s}px/1.35 Plex, Arial;color:${c}">${t}</div>`).join("")}
    <div style="position:absolute;left:${cx - sz/2}px;top:${cy - sh/2}px;transform:rotate(-8deg)">${stampSVG(st, sz)}</div></div>`;
}).join("");
fs.writeFileSync(M + "paste.html", `<!doctype html><meta charset=utf-8><style>${css} body{margin:0;background:#000}</style>${body}`);
const { chromium } = await import("/Users/simondavis/.npm/_npx/e41f203b7505f1fb/node_modules/playwright/index.mjs");
const b = await chromium.launch(); const pg = await b.newPage({ viewport: { width: 1200, height: 1000 } });
await pg.goto("file://" + M + "paste.html"); await pg.evaluate(() => document.fonts.ready); await pg.waitForTimeout(1000);
// the reader card's logo cover takes the band colour under it
await pg.evaluate(() => { const i = document.querySelector("#reader-link img"); const c = document.createElement("canvas"); c.width = 1200; c.height = 630; const x = c.getContext("2d"); x.drawImage(i, 0, 0); const d = x.getImageData(900, 5, 1, 1).data; document.querySelectorAll("#reader-link .cv")[0].style.background = `rgb(${d[0]},${d[1]},${d[2]})`; });
for (const c of cards) await (await pg.$("#" + c[0])).screenshot({ path: M + "paste-" + c[0] + ".png" });
await b.close(); console.log("ok");
