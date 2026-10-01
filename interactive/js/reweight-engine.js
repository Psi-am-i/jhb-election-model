// The "play with the model" engine: src/reweight.py under Pyodide, driven by
// pyboot/page.py. There is no JavaScript re-weighting anywhere; every figure
// the page shows is the Python's return value (SPEC-v2 Lane P, INTEGRATION §3b).
//
// Runs inside the page's Web Worker (js/model-worker.js) and, unchanged, under
// node in interactive/tests/page.test.mjs, which is why its inputs are
// injectable:
//   loadPyodide(opts)   Pyodide's loader
//   readText(rel)       text of a file relative to interactive/ ("py/x.py")
//   readBytes(rel)      bytes of `${drawsDir}/<file>`, as a Uint8Array; the node
//                       test reads from the repository root with the default
//                       drawsDir ("site/draws/base.bin"), the Worker from the
//                       draws directory itself with drawsDir "."
//
// The Python is the served copy in interactive/py/page/, written by
// tools/sync_py.mjs; its manifest names the files and their hash, and a copy
// whose hash disagrees is refused rather than run.

export const PYODIDE_URL = "https://cdn.jsdelivr.net/pyodide/v0.29.5/full/";
const PAGE_DIR = "/page";

export class PageCodeMissing extends Error {}

export async function loadReweightEngine({ onStage = () => {}, loadPyodide, readText, readBytes,
                                           indexURL = PYODIDE_URL, drawsDir = "site/draws" } = {}) {
  const t0 = performance.now();
  const times = {};
  const mark = (k, label) => { times[k] = Math.round(performance.now() - t0); onStage(k, label, times[k]); };

  const code = (async () => {
    let manifest;
    try { manifest = JSON.parse(await readText("py/manifest.json")); }
    catch (e) {
      throw new PageCodeMissing("The re-weighting code is not being served (interactive/py/manifest.json is missing). " +
        "Run `node interactive/tools/sync_py.mjs` and reload.");
    }
    if (!manifest.page) throw new PageCodeMissing("interactive/py/manifest.json predates the page code. Run `node interactive/tools/sync_py.mjs`.");
    const { dir, files, data, boot } = manifest.page;
    const all = [...files, ...data, "page_code_ref.py"];
    const texts = await Promise.all(all.map(async f => [f, await readText(`py/${dir}/${f}`)]));
    return { manifest, texts, boot: await readText(boot) };
  })();
  const index = (async () => JSON.parse(new TextDecoder().decode(await readBytes(`${drawsDir}/index.json`))))();

  onStage("start", "Loading Python", 0);
  const py = await loadPyodide({ indexURL });
  mark("pyodide", "Loading numpy");
  await py.loadPackage("numpy", { messageCallback: () => {} });
  mark("numpy", "Loading the model's re-weighting");
  const { manifest, texts, boot } = await code;
  py.FS.mkdirTree(PAGE_DIR);
  for (const [f, text] of texts) {
    const parts = f.split("/");
    if (parts.length > 1) py.FS.mkdirTree(`${PAGE_DIR}/${parts.slice(0, -1).join("/")}`);
    py.FS.writeFile(`${PAGE_DIR}/${f}`, text);
  }
  py.runPython(`import os, sys\nos.chdir(${JSON.stringify(PAGE_DIR)})\nif ${JSON.stringify(PAGE_DIR)} not in sys.path: sys.path.insert(0, ${JSON.stringify(PAGE_DIR)})`);
  py.runPython(boot);
  const pageRef = py.runPython("import page_code_ref; page_code_ref.PAGE_REF");
  if (pageRef !== manifest.page.code_ref)
    throw new Error(`the served page code does not match its manifest (${pageRef} vs ${manifest.page.code_ref})`);
  const loadCellPy = py.globals.get("load_cell");
  const computePy = py.globals.get("compute");
  const poolsPy = py.globals.get("pools_of");
  mark("import", "Loading the published draws");

  const { cells } = await index;
  const loaded = new Map();
  // One cell, fetched only when first chosen (SPEC-v2: lazily per cell).
  async function loadCell(path) {
    if (!loaded.has(path)) {
      loaded.set(path, (async () => {
        const dir = path === "." ? drawsDir : `${drawsDir}/${path}`;
        const [m, blob] = await Promise.all([readBytes(`${dir}/manifest.json`), readBytes(`${dir}/base.bin`)]);
        const r = loadCellPy(path, new TextDecoder().decode(m), blob);
        const out = r.toJs({ dict_converter: Object.fromEntries });
        r.destroy();
        return out;
      })());
    }
    return loaded.get(path);
  }
  const base = await loadCell(".");
  mark("draws", "Ready");

  function toJS(proxyOrValue) {
    if (proxyOrValue && typeof proxyOrValue.toJs === "function") {
      const v = proxyOrValue.toJs({ dict_converter: Object.fromEntries });
      proxyOrValue.destroy();
      return v;
    }
    return proxyOrValue;
  }
  // The poll set is chosen at build time and served in index.json (page.py set_polls).
  py.globals.get("set_polls")(JSON.stringify((await index).polls || []));
  const polls = JSON.parse(py.runPython("import json\njson.dumps(polls())"));
  const pools = toJS(poolsPy("."));

  // Every figure for one setting. Loads the chosen cell first if needed.
  async function compute(settings) {
    await loadCell(settings.cell || ".");
    if ((settings.cell || ".") !== ".") await loadCell(".");
    return JSON.parse(computePy(JSON.stringify(settings)));
  }

  // The by-election evidence column (DESIGN-decided §11), selected at build
  // time by export_draws --index from the model's own input file.
  const byelection = (await index).byelection ?? null;
  return { compute, loadCell, cells, base, polls, pools, pageRef, times, byelection,
           modelVersion: base.model_version };
}
