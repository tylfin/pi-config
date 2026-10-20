#!/usr/bin/env node
// Minimal Chrome DevTools Protocol driver for a configure-browser session.
// Zero dependencies: uses Node 22+ global fetch and WebSocket.

import { writeFileSync } from "node:fs";

const USAGE = `Usage: cdp.mjs [--port N] [--tab ID|URL_SUBSTRING] <command> [args]

Commands:
  tabs                         List page tabs (id, url, title)
  new [url]                    Open a new tab and print its id
  close                        Close the selected tab
  goto <url>                   Navigate and wait for the page to settle
  url                          Print the current URL and title
  text [selector] [--max N]    Print innerText (default body, max 20000 chars)
  eval <expression>            Evaluate JS in the page (awaits promises), print JSON
  wait <selector|text:...>     Wait until a selector or visible text appears (--timeout ms)
  click <selector|text:...>    Click the first matching element
  type <selector> <text>       Focus an input and insert text
  press <key>                  Send a key (Enter, Escape, Tab, ArrowDown, ...)
  screenshot <path> [--full]   Save a PNG screenshot

Options:
  --port N      CDP port (default $CDP_PORT or 9222)
  --tab X       Tab id or URL substring (default: first http(s) page)
  --timeout ms  Timeout for goto/wait/click (default 30000)`;

const args = process.argv.slice(2);
const opts = { port: process.env.CDP_PORT || "9222", tab: null, timeout: 30000, max: 20000, full: false };
const positional = [];
for (let i = 0; i < args.length; i++) {
  const a = args[i];
  if (a === "--port") opts.port = args[++i];
  else if (a === "--tab") opts.tab = args[++i];
  else if (a === "--timeout") opts.timeout = Number(args[++i]);
  else if (a === "--max") opts.max = Number(args[++i]);
  else if (a === "--full") opts.full = true;
  else if (a === "-h" || a === "--help") { console.log(USAGE); process.exit(0); }
  else positional.push(a);
}
const [cmd, ...rest] = positional;
if (!cmd) { console.error(USAGE); process.exit(2); }

const base = `http://localhost:${opts.port}`;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function listPages() {
  const res = await fetch(`${base}/json/list`).catch(() => null);
  if (!res) throw new Error(`No browser on ${base}. Start one with configure-browser --detached --json.`);
  return (await res.json()).filter((t) => t.type === "page");
}

async function pickTab() {
  const pages = await listPages();
  if (opts.tab) {
    const t = pages.find((p) => p.id === opts.tab) || pages.find((p) => p.url.includes(opts.tab));
    if (!t) throw new Error(`No tab matches "${opts.tab}"`);
    return t;
  }
  const t = pages.find((p) => /^https?:/.test(p.url)) || pages[0];
  if (!t) throw new Error("No page tabs open. Use: cdp.mjs new <url>");
  return t;
}

function connect(wsUrl) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(wsUrl);
    let id = 0;
    const pending = new Map();
    const listeners = new Set();
    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.id && pending.has(msg.id)) {
        const { res, rej } = pending.get(msg.id);
        pending.delete(msg.id);
        msg.error ? rej(new Error(msg.error.message)) : res(msg.result);
      } else if (msg.method) listeners.forEach((fn) => fn(msg));
    };
    ws.onerror = () => reject(new Error(`Cannot connect to ${wsUrl}`));
    ws.onopen = () =>
      resolve({
        send: (method, params = {}) =>
          new Promise((res, rej) => {
            const n = ++id;
            pending.set(n, { res, rej });
            ws.send(JSON.stringify({ id: n, method, params }));
          }),
        on: (fn) => listeners.add(fn),
        close: () => ws.close(),
      });
  });
}

async function evaluate(s, expression) {
  const r = await s.send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true, userGesture: true });
  if (r.exceptionDetails) {
    const d = r.exceptionDetails;
    throw new Error(d.exception?.description || d.text || "Evaluation failed");
  }
  return r.result.value;
}

// Resolves "text:Foo" to a visible element by its text (exact match first, then substring),
// preferring clickable elements. Anything else is treated as a CSS selector.
const finder = (target) => `(() => {
  const t = ${JSON.stringify(target)};
  const visible = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  if (!t.startsWith("text:")) return [...document.querySelectorAll(t)].find(visible) || null;
  const needle = t.slice(5).trim().toLowerCase();
  const label = (el) => (el.innerText || el.value || el.getAttribute("aria-label") || "").trim().toLowerCase();
  const clickable = "a,button,[role=button],[role=tab],[role=menuitem],[role=option],[role=link],input,label,summary";
  const els = [...document.querySelectorAll("body *")].filter(visible);
  for (const match of [(s) => s === needle, (s) => s.includes(needle)]) {
    const hits = els.filter((el) => match(label(el)));
    const inner = hits.filter((el) => !hits.some((o) => o !== el && el.contains(o)));
    const pick = inner.find((el) => el.closest(clickable)) || inner[0];
    if (pick) return pick.closest(clickable) || pick;
  }
  return null;
})()`;

async function waitFor(s, target) {
  const deadline = Date.now() + opts.timeout;
  while (Date.now() < deadline) {
    if (await evaluate(s, `!!${finder(target)}`)) return;
    await sleep(250);
  }
  throw new Error(`Timed out after ${opts.timeout}ms waiting for ${target}`);
}

async function settle(s) {
  const deadline = Date.now() + opts.timeout;
  while (Date.now() < deadline && (await evaluate(s, "document.readyState").catch(() => "loading")) !== "complete") {
    await sleep(200);
  }
  // Datadog pages are SPAs that keep fetching after load; give them a moment to render.
  await sleep(1500);
}

async function main() {
  if (cmd === "tabs") {
    for (const p of await listPages()) console.log(`${p.id}\t${p.url}\t${p.title}`);
    return;
  }
  if (cmd === "new") {
    const res = await fetch(`${base}/json/new?${encodeURI(rest[0] || "about:blank")}`, { method: "PUT" });
    const t = await res.json();
    console.log(t.id);
    return;
  }

  const tab = await pickTab();
  if (cmd === "close") {
    await fetch(`${base}/json/close/${tab.id}`);
    return;
  }

  const s = await connect(tab.webSocketDebuggerUrl);
  try {
    switch (cmd) {
      case "goto": {
        if (!rest[0]) throw new Error("goto needs a URL");
        await s.send("Page.navigate", { url: rest[0] });
        await sleep(300);
        await settle(s);
        const info = await evaluate(s, "({ url: location.href, title: document.title })");
        console.log(`${info.url}\t${info.title}`);
        if (/\/account\/login|\/signin|accounts\.google\.com/.test(info.url)) {
          console.error("Landed on a login page: the session is missing or expired for this site.");
          process.exitCode = 1;
        }
        break;
      }
      case "url": {
        const info = await evaluate(s, "({ url: location.href, title: document.title })");
        console.log(`${info.url}\t${info.title}`);
        break;
      }
      case "text": {
        const sel = rest[0] || "body";
        const out = await evaluate(s, `(document.querySelector(${JSON.stringify(sel)})?.innerText ?? null)`);
        if (out === null) throw new Error(`No element matches ${sel}`);
        console.log(out.length > opts.max ? `${out.slice(0, opts.max)}\n[truncated ${out.length - opts.max} chars]` : out);
        break;
      }
      case "eval": {
        const v = await evaluate(s, rest.join(" "));
        console.log(typeof v === "string" ? v : JSON.stringify(v, null, 2));
        break;
      }
      case "wait":
        await waitFor(s, rest[0]);
        console.log("found");
        break;
      case "click": {
        await waitFor(s, rest[0]);
        await evaluate(s, `(() => { const el = ${finder(rest[0])}; el.scrollIntoView({ block: "center" }); el.click(); })()`);
        await sleep(500);
        console.log("clicked");
        break;
      }
      case "type": {
        await waitFor(s, rest[0]);
        // Replace existing content in inputs and contenteditable search bars (DRUIDS uses the latter).
        await evaluate(s, `(() => {
          let el = ${finder(rest[0])};
          el = el.matches("input,textarea,[contenteditable]") ? el : el.querySelector("input,textarea,[contenteditable]") || el;
          el.focus();
          if ("select" in el) el.select();
          else { const r = document.createRange(); r.selectNodeContents(el); getSelection().removeAllRanges(); getSelection().addRange(r); }
        })()`);
        await s.send("Input.insertText", { text: rest.slice(1).join(" ") });
        console.log("typed");
        break;
      }
      case "press": {
        const key = rest[0];
        const codes = { Enter: 13, Escape: 27, Tab: 9, Backspace: 8, ArrowUp: 38, ArrowDown: 40, ArrowLeft: 37, ArrowRight: 39 };
        const base = { key, code: key, windowsVirtualKeyCode: codes[key] || 0, text: key === "Enter" ? "\r" : undefined };
        await s.send("Input.dispatchKeyEvent", { type: "keyDown", ...base });
        await s.send("Input.dispatchKeyEvent", { type: "keyUp", ...base });
        console.log("pressed");
        break;
      }
      case "screenshot": {
        if (!rest[0]) throw new Error("screenshot needs an output path");
        const r = await s.send("Page.captureScreenshot", { format: "png", captureBeyondViewport: opts.full });
        writeFileSync(rest[0], Buffer.from(r.data, "base64"));
        console.log(rest[0]);
        break;
      }
      default:
        throw new Error(`Unknown command: ${cmd}\n\n${USAGE}`);
    }
  } finally {
    s.close();
  }
}

main().catch((e) => {
  console.error(e.message);
  process.exit(1);
});
