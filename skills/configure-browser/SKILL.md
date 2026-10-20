---
name: configure-browser
description: Open and drive a Chrome browser that is already logged in to Datadog's internal sites (prod app.datadoghq.com and staging dd.datad0g.com) using the configure-browser CLI. Use when you need to view, screenshot, read, or click through the Datadog web UI as the user, verify a frontend change, or load a page with feature flags, test drives, or mock-proxy rules.
compatibility: macOS with Google Chrome, configure-browser on PATH, Doggo Chrome extension, Node 22+ for scripts/cdp.mjs.
---

# configure-browser

`configure-browser` launches a separate Chrome with the user's Datadog session copied in, and exposes it over the Chrome DevTools Protocol (CDP). `scripts/cdp.mjs` (zero dependencies) drives that browser from bash.

For data questions (metrics, logs, monitors), prefer the Datadog MCP tools or APIs. Use the browser when you need what the UI shows.

## Safety

- The browser is logged in as the user, in production. Treat it as read-only. Do not click anything that creates, edits, mutes, resolves, deletes, or saves without the user's explicit approval.
- Do not print `document.cookie`, local storage, or hidden inputs. Datadog pages embed a CSRF token and user JSON in hidden inputs. Scope `eval` and `text` to what you need.
- Do not run `configure-browser export-storage` unless asked. Never commit or share the file it writes.

## 1. Start (or reuse) a browser

Check for a browser you already started this session first: `curl -s localhost:<port>/json/version`.

Port 9222 is often used by the user's own session. Do not kill or reuse a browser you did not start; pick another port (e.g. 9333).

```bash
configure-browser --session-source doggo --detached --json --port 9333 \
  --url https://dd.datad0g.com/monitors
```

- Set the bash timeout to at least 90s. Doggo sends the session about once a minute (default wait 75s, `--doggo-timeout`). Telling the user to open the Doggo popup in Chrome sends it immediately.
- Output is one JSON document. Check `"authenticated": true` and record `port` and `pid`. The `pid_file` is shared and overwritten by every detached run, so rely on the `pid` from the JSON.
- On error the CLI prints the full usage text; the actual error is the last line of stderr.
- Without `--detached` it blocks until Ctrl+C. Agents should always use `--detached`.

Sites:
- Staging: `https://dd.datad0g.com`. Prod: `https://app.datadoghq.com`. One browser has sessions for both; navigate freely between them.
- Doggo also covers devlocal hosts (e.g. `https://app-dev-local-8444.datadoghq.com`) and the preview host of `--url`.
- Any other site (e.g. `ddstaging.datadoghq.com`, other regions): use `--session-source chrome` instead. It reads the Chrome cookie DB and may trigger a macOS Keychain prompt the user must approve.

Optional flags applied before the app loads (repeatable):
- `--experiment my_flag=true`, `--test-drive <name>`, `--disable-permission <perm>`
- `--mock-proxy-rule GET:/api/foo=http://localhost:9000`, `--target-override proto:src=dst`

To change these flags, `kill <pid>` and relaunch with the new flags. Detached mode fails if the port is in use. Run `configure-browser --help` for anything else.

## 2. Drive it

Set `CDP_PORT` once so you do not repeat `--port`. Resolve `scripts/` relative to this skill directory.

```bash
export CDP_PORT=9333
S=<skill-dir>/scripts/cdp.mjs
$S tabs                                   # id, url, title of each tab
$S goto https://app.datadoghq.com/apm/home
$S url
$S text --max 4000                        # body innerText, truncated
$S text 'main' --max 4000                 # scope to a selector
$S screenshot /tmp/page.png               # then view it with the read tool
$S click 'text:Triggered'                 # by visible text (exact match first)
$S click 'button[aria-label="Close"]'     # or by CSS selector
$S type '[placeholder="Filter monitors"]' 'status:alert' && $S press Enter
$S wait 'text:Showing'                    # wait for content (--timeout ms)
$S eval 'document.querySelectorAll("table tr").length'
$S new https://dd.datad0g.com/logs        # extra tab; select with --tab <id|url-substring>
```

Tips:
- Datadog pages are SPAs. `goto` waits for load plus a short delay; use `wait` for specific content before reading. Many filters live in the URL (`?q=...`), so navigating to a URL is often more reliable than clicking.
- Without `--tab`, commands use the first http(s) tab, which may be the newest. Pass `--tab` when more than one tab is open.
- DRUIDS search bars are `contenteditable` divs with a `placeholder` attribute, not `<input>`. Target `[placeholder="..."]`.
- `goto` exits 1 if it lands on a login page. Ask the user to log in to that site in their normal Chrome, then relaunch.
- If `agent-browser` or Playwright is installed, they can attach instead: `agent-browser connect <port>` or `chromium.connectOverCDP("http://localhost:<port>")`.

## 3. Clean up

When finished, `kill <pid>` for each browser you started. Leave browsers you did not start alone.
