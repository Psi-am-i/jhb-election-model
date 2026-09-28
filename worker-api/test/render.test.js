// /f/<id> is rendered on the server with Open Graph tags, and the card PNG is
// rendered on the server from the stored forecast.
import { describe, it, expect } from "vitest";
import { env } from "cloudflare:test";
import { exports } from "cloudflare:workers";
import { forecastPage, cardSVG, renderPNG, cardKey } from "../src/render.js";
import { schema, geom } from "../src/forecasts.js";
import { validateForecast } from "../src/validate.js";
import { fakeSeats } from "./fake-seats.js";
import { makeUser, api, validForecast } from "./helpers.js";

const worker = exports.default;

// A fixed stored row: validated body, seats from the test double, fixed dates.
async function fixedRow(name = "Thandi & \"Sipho\" O'Neill") {
  const body = validateForecast({ ...validForecast(), display_name: name }, schema).value;
  const seats = await (await fakeSeats(new Request("https://seats/v1/seats", { method: "POST",
    body: JSON.stringify({ ward_calls: body.ward_calls, pr_share: body.pr_share, council_seats: schema["x-council"].council_seats }) }))).json();
  return { id: "Snap5hot01", rev: 3, body: JSON.stringify(body), seats: JSON.stringify(seats), seats_code_ref: seats.code_ref,
    created_at: "2026-10-01T08:00:00.000Z", updated_at: "2026-10-02T08:00:00.000Z", model_ref: body.model_ref };
}

function pngSize(u8) {
  expect(Array.from(u8.slice(0, 8))).toEqual([137, 80, 78, 71, 13, 10, 26, 10]);
  const dv = new DataView(u8.buffer, u8.byteOffset);
  return [dv.getUint32(16), dv.getUint32(20)];
}

describe("server-rendered share page", () => {
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

describe("server-rendered card", () => {
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
