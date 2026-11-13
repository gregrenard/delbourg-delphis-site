#!/usr/bin/env python3
"""Gate (l): mobile / tablet / desktop layout check in BOTH languages, headless, no manual step.

For every pre-rendered page (index.html + the six content pages), every width in WIDTHS and
every language in LANGS, load the page inside an <iframe> of exactly that width and measure,
after the runtime has rendered:
  - horizontal scroll: documentElement.scrollWidth must equal clientWidth;
  - visible overflow: no element whose right edge passes the viewport unless an ancestor
    clips it (overflow hidden/clip/auto/scroll), which is the case for ellipsis text;
  - the runtime rendered: #dc-root exists and has a non-empty <h1>;
  - the language really switched: <html lang> equals the requested language and the header
    carries that language's nav label ("Speaking" in EN, "Conférences" in FR) and not the other's;
  - no visible {{ }} placeholders (WARN: a content gap in Design, not a layout bug).

Languages: the site has no per-language URL, each page reads localStorage `mdd_lang` in
componentDidMount. The serving handler injects `localStorage.setItem('mdd_lang', <lang>)` as the
very first thing in <head> (before support.js), only for ?__layout=1&__lang=xx, so the runtime
starts in that language exactly as it does for a returning visitor who chose it.

Why an iframe: headless Chrome cannot make a window narrower than 500 px, so a
`--window-size=390` screenshot is a 500 px layout cropped, which fakes an overflow. An iframe
gives a true 390 px viewport.

Nothing is written to the repo: the measuring script is added to the HTML as it is served.

Usage (from the repo root):  python3 .claude/skills/sync-marylene-site/check-layout.py
Exit 1 if any page overflows, fails to render or fails to switch language at any width.
"""
import html
import json
import os
import re
import subprocess
import sys
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from manifest import prerender_files  # noqa: E402

WIDTHS = [390, 768, 1440]
LANGS = ["en", "fr"]
CHROME = os.environ.get("CHROME") or "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
REPO = os.getcwd()

PROBE = r"""<script>
setTimeout(function () {
  var W = document.documentElement.clientWidth, SW = document.documentElement.scrollWidth, out = [];
  var L = /__lang=fr/.test(location.search) ? 'fr' : 'en';
  var want = L === 'fr' ? 'Conférences' : 'Speaking', other = L === 'fr' ? 'Speaking' : 'Conférences';
  function clipped(e) {
    for (var a = e.parentElement; a && a !== document.body; a = a.parentElement) {
      var o = getComputedStyle(a).overflowX;
      if (o === 'hidden' || o === 'clip' || o === 'auto' || o === 'scroll') return true;
    }
    return false;
  }
  var root = document.getElementById('dc-root');
  (root ? root.querySelectorAll('*') : []).forEach(function (e) {
    if (e instanceof SVGElement) return;
    var r = e.getBoundingClientRect();
    if (r.width > 0 && r.right > W + 1 && !clipped(e))
      out.push(e.tagName + ' right=' + Math.round(r.right) + ' "' + (e.textContent || '').trim().slice(0, 50) + '"');
  });
  var h1 = root && root.querySelector('h1');
  var hd = root && root.querySelector('header');
  var nav = hd ? hd.textContent : '';
  var ph = ((root && root.innerText) || '').match(/\{\{[^}]*\}\}/g) || [];
  parent.postMessage(JSON.stringify({
    W: W, SW: SW, h1: !!(h1 && h1.textContent.trim()), placeholders: ph.length, over: out.slice(0, 8),
    lang: document.documentElement.lang, navOk: nav.indexOf(want) >= 0 && nav.indexOf(other) < 0
  }), '*');
}, 6000);
</script>"""

HARNESS = """<!doctype html><html><body style="margin:0">
<iframe src="/{page}?__layout=1&__lang={lang}" style="width:{w}px;height:900px;border:0"></iframe>
<pre id="OUT"></pre>
<script>addEventListener('message', function (m) {{ document.getElementById('OUT').textContent = m.data; }});</script>
</body></html>"""


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        path, _, query = self.path.partition("?")
        if path == "/__harness":
            q = dict(p.split("=", 1) for p in query.split("&") if "=" in p)
            body = HARNESS.format(page=q.get("page", "index.html"), w=int(q.get("w", "390")),
                                  lang=q.get("lang", "en")).encode()
            return self._send(body)
        if "__layout=1" in query and path.endswith(".html"):
            f = os.path.join(REPO, path.lstrip("/"))
            if os.path.isfile(f):
                lang = "fr" if "__lang=fr" in query else "en"
                pre = "<script>try{localStorage.setItem('mdd_lang','%s')}catch(e){}</script>" % lang
                s = open(f, encoding="utf-8").read()
                s = s.replace("<head>", "<head>" + pre, 1).replace("</body>", PROBE + "</body>", 1)
                return self._send(s.encode("utf-8"))
        if path.lower().endswith((".mp4", ".webm", ".mov", ".m4v", ".ogv")):
            return self.send_error(404, "media blocked during layout check")
        return super().do_GET()

    def _send(self, body):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def measure(port, page, w, lang):
    url = "http://127.0.0.1:%d/__harness?page=%s&w=%d&lang=%s" % (port, page, w, lang)
    try:
        dom = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--dump-dom",
                              "--window-size=%d,1000" % max(w + 40, 600),
                              "--virtual-time-budget=14000", url],
                             capture_output=True, text=True, timeout=60).stdout
    except Exception as e:  # noqa: BLE001
        return None, "render error: %s" % e
    m = re.search(r'<pre id="OUT">(.*?)</pre>', dom or "", re.S)
    if not m or not m.group(1).strip():
        return None, "no measurement (page did not render in time)"
    return json.loads(html.unescape(m.group(1))), None


def main():
    if not os.path.exists(CHROME):
        print("  BAD: Chrome not found at %r, the layout gate cannot run" % CHROME)
        return 1
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), partial(Handler, directory=REPO))
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    bad = 0
    checked = 0
    try:
        for page in prerender_files():
            if not os.path.exists(page):
                print("  BAD: %s missing" % page); bad = 1; continue
            for lang in LANGS:
                for w in WIDTHS:
                    r, err = measure(port, page, w, lang)
                    label = "%s [%s] @%dpx" % (page, lang.upper(), w)
                    checked += 1
                    if err:
                        print("  BAD: %s: %s" % (label, err)); bad = 1; continue
                    if r["W"] != w:
                        print("  BAD: %s: viewport is %d px, not %d" % (label, r["W"], w)); bad = 1; continue
                    problems = []
                    if r["SW"] > r["W"]:
                        problems.append("horizontal scroll (scrollWidth %d > %d)" % (r["SW"], r["W"]))
                    if r["over"]:
                        problems.append("%d element(s) past the right edge: %s" % (len(r["over"]), "; ".join(r["over"][:3])))
                    if not r["h1"]:
                        problems.append("runtime did not render an <h1>")
                    if r["lang"] != lang:
                        problems.append("<html lang> is %r, expected %r" % (r["lang"], lang))
                    if not r["navOk"]:
                        problems.append("header is not in %s" % lang.upper())
                    if problems:
                        print("  BAD: %s: %s" % (label, " | ".join(problems))); bad = 1
                    else:
                        print("  ok: %s (no overflow, h1 rendered, language switched)" % label)
                    if r["placeholders"]:
                        print("  WARN: %s shows %d {{ }} placeholder(s) — fill them in Claude Design" % (label, r["placeholders"]))
    finally:
        httpd.shutdown()
        httpd.server_close()
    print("  => layout: %d renders (%d pages x %d widths x %d languages): %s"
          % (checked, len(prerender_files()), len(WIDTHS), len(LANGS), "FAIL" if bad else "pass"))
    return bad


if __name__ == "__main__":
    sys.exit(main())
