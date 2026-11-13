#!/usr/bin/env python3
"""Deploy-only transform: deployed slugs = the legacy Wix URLs.

Design names its pages About / Books / Speaking / Writings / Blog / Contact, but the
canonicals it ships (and the old www.delbourg-delphis.org on Wix) use /about, /book,
/speaking, /more, /blog, /contact. GitHub Pages is case-sensitive, so serving /About
while the canonical says /about would split the page in two for search engines and
break every inbound link from the Wix era. pages.json therefore carries the legacy
slug for each page, and this script makes the files agree with it:

  1. every internal link "<DesignName>.dc.html" becomes "<slug>.dc.html" (the
     seo-clean-urls.py stage then strips the extension, giving href="about");
  2. the pulled file <DesignName>.dc.html is renamed <slug>.dc.html. The rename goes
     through a temporary name because macOS is case-insensitive and About -> about is
     the same path to the filesystem.

Run from the repo root, AFTER the home-link rewrite and BEFORE seo-clean-urls.py.
Idempotent: once renamed there is nothing left to rewrite.
"""
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from manifest import PAGES  # noqa: E402

renames = []
for p in PAGES:
    if p["role"] != "content":
        continue
    stem = p["design"][: -len(".dc.html")]
    if stem != p["slug"]:
        renames.append((stem, p["slug"]))

files = glob.glob("*.dc.html") + (["index.html"] if os.path.exists("index.html") else [])
for f in files:
    s = open(f, encoding="utf-8").read()
    t = s
    for stem, slug in renames:
        for q in ('"', "'"):
            t = t.replace("%s%s.dc.html%s" % (q, stem, q), "%s%s.dc.html%s" % (q, slug, q))
    if t != s:
        open(f, "w", encoding="utf-8").write(t)
        print("slug-links: links rewritten in", f)

for stem, slug in renames:
    src, dst = stem + ".dc.html", slug + ".dc.html"
    if os.path.exists(src) and src != dst:
        tmp = dst + ".tmp-rename"
        os.rename(src, tmp)
        os.rename(tmp, dst)
        print("slug-links: %s -> %s" % (src, dst))
