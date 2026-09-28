// /f/<id> is rendered on the server with Open Graph tags, and the card PNG is
// rendered on the server from the stored forecast.
import { describe, it, expect } from "vitest";
import { env } from "cloudflare:test";
import { exports } from "cloudflare:workers";
import { forecastPage, cardSVG, renderPNG, cardKey } from "../src/render.js";
import { textWidth } from "../../interactive/js/card.js";
import { schema, geom } from "../src/forecasts.js";
import { validateForecast } from "../src/validate.js";
import { seatRequest } from "../src/seats.js";
import { fakeSeats } from "./fake-seats.js";
import { makeUser, api, validForecast } from "./helpers.js";

const worker = exports.default;

// A fixed stored row: validated body, seats from the test double, fixed dates.
async function fixedRow(name = "Thandi & \"Sipho\" O'Neill") {
  const body = validateForecast({ ...validForecast(), display_name: name }, schema).value;
  const seats = await (await fakeSeats(new Request("https://seats/v1/seats", { method: "POST",
    body: JSON.stringify(seatRequest(body, schema)) }))).json();
  return { id: "Snap5hot01", rev: 3, body: JSON.stringify(body), seats: JSON.stringify(seats), seats_code_ref: seats.code_ref,
    created_at: "2026-10-01T08:00:00.000Z", updated_at: "2026-10-02T08:00:00.000Z", model_ref: body.model_ref };
}

function pngSize(u8) {
  expect(Array.from(u8.slice(0, 8))).toEqual([137, 80, 78, 71, 13, 10, 26, 10]);
  const dv = new DataView(u8.buffer, u8.byteOffset);
  return [dv.getUint32(16), dv.getUint32(20)];
}

describe("server-rendered share page", () => {
  // RE-RECORDED 2026-09-28 with the card snapshot below: the embedded card SVG
  // changed layout, and the stored seats carry majority and excessive.
  it("matches the snapshot", async () => {
    const html = forecastPage(await fixedRow(), schema, geom, env);
    expect(html).toMatchSnapshot();
  });

  it("carries the Open Graph and Twitter tags crawlers read", async () => {
    const html = forecastPage(await fixedRow(), schema, geom, env);
    const url = `${env.SITE_ORIGIN}/f/Snap5hot01`;
    for (const tag of [
      `<meta property="og:url" content="${url}">`,
      `<meta property="og:image" content="${url}/card.png?v=3">`,
      `<meta property="og:image:width" content="1200">`,
      `<meta property="og:image:height" content="630">`,
      `<meta name="twitter:card" content="summary_large_image">`,
      `<link rel="canonical" href="${url}">`,
      `<meta name="robots" content="noindex">`,
    ]) expect(html).toContain(tag);
    expect(html).toMatch(/<meta property="og:title" content="Thandi &amp; &quot;Sipho&quot; O&#39;Neill&#39;s forecast for Johannesburg">/);
  });

  it("escapes the reader's name everywhere it appears", async () => {
    const html = forecastPage(await fixedRow(), schema, geom, env);
    expect(html).not.toContain(`"Sipho"`);
    expect(html).not.toContain(`O'Neill`);
  });

  it("says 'A reader' when no name was typed", async () => {
    const row = await fixedRow();
    const b = JSON.parse(row.body); b.display_name = null; row.body = JSON.stringify(b);
    expect(forecastPage(row, schema, geom, env)).toContain("<title>A reader&#39;s forecast · Johannesburg 2026</title>");
  });

  it("is served at /f/<id> with 200, and unknown ids answer 404", async () => {
    const u = await makeUser();
    const r = await worker.fetch(api("/api/forecasts", { method: "POST", body: validForecast(), headers: { cookie: u.cookie, "cf-connecting-ip": "198.51.100.7" } }));
    const { id } = await r.json();
    const page = await worker.fetch(new Request(`${env.SITE_ORIGIN}/f/${id}`));
    expect(page.status).toBe(200);
    expect(page.headers.get("content-type")).toMatch(/text\/html/);
    expect(await page.text()).toContain(`og:image" content="${env.SITE_ORIGIN}/f/${id}/card.png?v=1"`);
    expect((await worker.fetch(new Request(`${env.SITE_ORIGIN}/f/ZZZZZZZZZZ`))).status).toBe(404);
    expect((await worker.fetch(new Request(`${env.SITE_ORIGIN}/f/..%2F..`))).status).toBe(404);
  });
});

// Every bar row as drawn: the name's text, its size and x, and the bar's x.
function barRows(svg) {
  const re = /<text class="nm" x="([\d.]+)" y="[\d.]+" font-family="[^"]*" font-size="([\d.]+)" fill="[^"]*">([^<]*)<\/text><rect x="([\d.]+)"/g;
  const unesc = t => t.replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&#39;/g, "'");
  return [...svg.matchAll(re)].map(m => ({ x: +m[1], fs: +m[2], name: unesc(m[3]), bar: +m[4] }));
}
const overlaps = rows => rows.filter(r => r.x + textWidth(r.name, r.fs) > r.bar);

// A schema whose top parties carry long roster names, as a real IEC roster can.
function longNames(schema) {
  const s = clone(schema);
  const long = ["African Transformation Movement", "Patriotic Alliance of South Africa", "All Citizens Party"];
  s["x-parties"].forEach((p, i) => { p.name = long[i % long.length]; });
  return s;
}
const clone = o => JSON.parse(JSON.stringify(o));

describe("server-rendered card", () => {
  it("no party name runs into its bar, measured in the DejaVu the server renders with", async () => {
    const row = await fixedRow();
    for (const size of ["link", "story"]) {
      for (const sch of [schema, longNames(schema)]) {
        const rows = barRows(cardSVG(row, sch, geom, size));
        expect(rows.length).toBe(5);                    // it looked: the top five
        expect(overlaps(rows)).toEqual([]);
      }
    }
    // It can see: the same rows with each bar pulled left into its name.
    const rows = barRows(cardSVG(row, longNames(schema), geom, "link"));
    expect(overlaps(rows.map(r => ({ ...r, bar: r.x + 20 }))).length).toBe(5);
  });

  it("says the council the seat law returned, not a typed 270", async () => {
    const row = await fixedRow();
    const a = JSON.parse(row.seats);
    const first = Object.keys(a.seats)[0];
    a.seats[first] += 2; a.pr[first] += 2; a.council_total += 2; a.majority = Math.floor(a.council_total / 2) + 1;
    const svg = cardSVG({ ...row, seats: JSON.stringify(a) }, schema, geom, "link");
    expect(svg).toContain(`${a.council_total}-seat council`);
    expect(svg).not.toContain(`${schema["x-council"].council_seats}-seat council`);
    expect(svg).toMatch(new RegExp(` of ${a.council_total} seats`));
  });

  // RE-RECORDED 2026-09-28, deliberately: the card now lays text out by measured
  // DejaVu width (party names had run into their bars) and prints the council
  // from the seat answer. The new layout was checked by eye in rendered PNGs.
  it("the SVG comes from the page's own builder and matches the snapshot", async () => {
    const svg = cardSVG(await fixedRow(), schema, geom, "link");
    expect(svg.startsWith('<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630"')).toBe(true);
    expect(svg).toMatchSnapshot();
  });

  it("renders 1200x630 and 1080x1920 PNGs", async () => {
    const row = await fixedRow();
    expect(pngSize(await renderPNG(cardSVG(row, schema, geom, "link")))).toEqual([1200, 630]);
    expect(pngSize(await renderPNG(cardSVG(row, schema, geom, "story")))).toEqual([1080, 1920]);
  });

  it("draws text with the embedded fonts (a different name gives a different image)", async () => {
    const a = await renderPNG(cardSVG(await fixedRow("Aaaa"), schema, geom, "link"));
    const b = await renderPNG(cardSVG(await fixedRow("Wwww"), schema, geom, "link"));
    expect(a.every((x, i) => x === b[i])).toBe(false);
  });

  it("renders only the current rev; any other v redirects", async () => {
    const u = await makeUser();
    const r = await worker.fetch(api("/api/forecasts", { method: "POST", body: validForecast(), headers: { cookie: u.cookie, "cf-connecting-ip": "198.51.100.8" } }));
    const { id } = await r.json();
    const bad = await worker.fetch(new Request(`${env.SITE_ORIGIN}/f/${id}/card.png?v=99`), { redirect: "manual" });
    expect(bad.status).toBe(302);
    expect(bad.headers.get("location")).toBe(`/f/${id}/card.png?v=1`);
    const ok = await worker.fetch(new Request(`${env.SITE_ORIGIN}/f/${id}/card.png?v=1`));
    expect(ok.status).toBe(200);
    expect(ok.headers.get("cache-control")).toBe("public, max-age=31536000, immutable");
    expect(pngSize(new Uint8Array(await ok.arrayBuffer()))).toEqual([1200, 630]);
  });

  it("the R2 key carries the rev and the seat code, so a seat-code change cannot reuse a stale card", async () => {
    const row = await fixedRow();
    expect(cardKey(row, "link")).toBe(`cards/Snap5hot01/3-${row.seats_code_ref.slice(0, 16)}/link.png`);
    expect(cardKey({ ...row, seats_code_ref: "0".repeat(32) }, "link")).not.toBe(cardKey(row, "link"));
  });
});
