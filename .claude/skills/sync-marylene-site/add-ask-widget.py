#!/usr/bin/env python3
"""Deploy-only transform: load the "Ask your AI" script (ask-your-ai.js) on every page except 404.html.

The script builds the corner box and the contact popup on its own and is generated outside Claude Design
(kit source: .works/ask-config.json, built with the ask-your-ai skill). Each Design sync wipes the <script>
tag, so this step puts it back before </body>. Relative path: the preview is served from a sub-path.
Idempotent.
"""
import glob, os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
TAG = '<script src="ask-your-ai.js" defer></script>'
n = 0
for p in sorted(glob.glob("*.html")):
    if p == "404.html":
        continue
    s = open(p, encoding="utf-8").read()
    if "ask-your-ai.js" in s or "</body>" not in s:
        continue
    open(p, "w", encoding="utf-8").write(s.replace("</body>", TAG + "</body>", 1)); n += 1
print("ask widget: script tag added on %d page(s); %d page(s) carry it" % (n, sum("ask-your-ai.js" in open(p, encoding="utf-8").read() for p in glob.glob("*.html"))))
