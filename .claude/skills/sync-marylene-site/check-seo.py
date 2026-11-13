#!/usr/bin/env python3
"""Gate (m): SEO + LLM-SEO checks on the deployed files. No browser.

Per page (index.html + the six content pages from pages.json):
  - <title> and meta description present, sane length (WARN outside 30–70 / 70–170 chars);
  - canonical present and EQUAL to the URL the page is deployed at (pages.json site + slug).
    This is the check that caught Design's lowercase Wix slugs vs the capitalised file names;
  - Open Graph (title, description, url = canonical, image) and Twitter card + image present;
  - og:image: a local file must be 1200 x 630; a hotlinked one (Wix) is a WARN, because the
    image dies the day the Wix account does;
  - JSON-LD parses; Home has Person (name, url, sameAs) and WebSite; every sub-page has a
    BreadcrumbList; /book has two Book entries;
  - favicon and apple-touch-icon referenced and present;
  - robots meta matches the mode in pages.json: noindex in draft, index after launch.
Site-wide:
  - robots.txt allows the AI / LLM crawlers (GPTBot, OAI-SearchBot, ClaudeBot,
    PerplexityBot, Google-Extended) and declares the sitemap;
  - llms.txt is well-formed (H1, > summary, ## Pages) and names Marylene;
  - images hotlinked from third-party hosts are listed (WARN) so the dependency is visible.

The book site's "no real client name" hash guardrail is deliberately NOT carried over: it
protects that book's client, and nothing on this site refers to one.

Usage (from the repo root):  python3 .claude/skills/sync-marylene-site/check-seo.py
Exit 1 on any BAD; WARN never fails, except that a canonical mismatch is BAD once launched.
"""
import json
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from manifest import DRAFT, PAGES, SITE, prerender_files  # noqa: E402

AI_BOTS = ["GPTBot", "OAI-SearchBot", "ClaudeBot", "PerplexityBot", "Google-Extended"]
NAME = "Marylene Delbourg-Delphis"
SLUGS = {p["design"]: p["slug"] for p in PAGES}

bad = 0


def say(ok, msg, warn=False):
    global bad
    if ok:
        print("  ok: " + msg)
    elif warn:
        print("  WARN: " + msg)
    else:
        print("  BAD: " + msg)
        bad = 1


def meta(head, attr, name):
    m = re.search(r'<meta %s="%s" content="([^"]*)"' % (attr, re.escape(name)), head)
    return m.group(1) if m else None


def png_size(path):
    with open(path, "rb") as f:
        h = f.read(24)
    if h[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", h[16:24])


def ld_types(head):
    out = []
    for block in re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', head, re.S):
        try:
            out.append(json.loads(block))
        except ValueError as e:
            say(False, "JSON-LD does not parse: %s" % e)
    return out


external = {}
for page in prerender_files():
    if not os.path.exists(page):
        say(False, "%s missing" % page)
        continue
    slug = page[: -len(".html")]
    expected = SITE + "/" if slug == "index" else "%s/%s" % (SITE, slug)
    s = open(page, encoding="utf-8").read()
    head = s.split("<body", 1)[0]
    t = re.search(r"<title>(.*?)</title>", head, re.S)
    title = t.group(1).strip() if t else ""
    desc = meta(head, "name", "description") or ""
    say(bool(title), "%s <title> present" % page)
    say(30 <= len(title) <= 70, "%s title length %d (30–70 recommended)" % (page, len(title)), warn=True)
    say(bool(desc), "%s meta description present" % page)
    say(70 <= len(desc) <= 170, "%s description length %d (70–170 recommended)" % (page, len(desc)), warn=True)
    canon = re.search(r'rel="canonical" href="([^"]*)"', head)
    got = canon.group(1) if canon else ""
    say(got == expected, "%s canonical is the deployed URL (%s)" % (page, expected) +
        ("" if got == expected else ", found %r" % got), warn=DRAFT)
    for prop in ("og:title", "og:description", "og:url", "og:image"):
        say(meta(head, "property", prop) is not None, "%s %s" % (page, prop))
    say(meta(head, "property", "og:url") in (None, got), "%s og:url equals canonical" % page, warn=DRAFT)
    say(meta(head, "name", "twitter:card") == "summary_large_image", "%s twitter:card summary_large_image" % page)
    say(meta(head, "name", "twitter:image") is not None, "%s twitter:image" % page)
    img = meta(head, "property", "og:image") or ""
    local = img.split(SITE + "/", 1)[-1] if img.startswith(SITE) else ""
    if local:
        if os.path.exists(local):
            size = png_size(local)
            say(size == (1200, 630), "%s og:image %s is %s (1200x630 expected)" % (page, local, size))
        else:
            say(False, "%s og:image does not resolve to a local file: %s" % (page, img))
    elif img:
        host = re.sub(r"^https?://([^/]+).*", r"\1", img)
        say(False, "%s og:image is hotlinked from %s (dies with that host)" % (page, host), warn=True)
    for u in re.findall(r'<img[^>]+src="(https?://[^"]+)"', s):
        external.setdefault(re.sub(r"^https?://([^/]+).*", r"\1", u), set()).add(u)

    docs = ld_types(head)
    types = {d.get("@type") for d in docs}
    if slug == "index":
        person = next((d for d in docs if d.get("@type") == "Person"), None)
        say(bool(person) and person.get("name") == NAME and person.get("url") and person.get("sameAs"),
            "%s JSON-LD Person (name, url, sameAs)" % page)
        say("WebSite" in types, "%s JSON-LD WebSite" % page)
    else:
        say("BreadcrumbList" in types, "%s JSON-LD BreadcrumbList" % page)
        if slug == "book":
            say(sum(1 for d in docs if d.get("@type") == "Book") == 2, "%s JSON-LD: two Book entries" % page)
    for rel, f in (("icon", "assets/favicon.png"), ("apple-touch-icon", "assets/apple-touch-icon.png")):
        say(('rel="%s"' % rel) in head and os.path.exists(f), "%s %s referenced and present" % (page, rel))
    robots = meta(head, "name", "robots") or ""
    say(robots.startswith("noindex") if DRAFT else robots == "index, follow",
        "%s robots meta '%s' matches mode (%s)" % (page, robots, "draft" if DRAFT else "launched"))

for host, urls in sorted(external.items()):
    say(False, "%d image(s) hotlinked from %s: copy them into assets/ before leaving that host" % (len(urls), host),
        warn=True)

txt = open("robots.txt", encoding="utf-8").read()
for bot in AI_BOTS:
    say(re.search(r"User-agent: %s\s*\nAllow: /" % re.escape(bot), txt) is not None, "robots.txt allows %s" % bot)
say("Sitemap: %s/sitemap.xml" % SITE in txt, "robots.txt declares the sitemap")

llms = open("llms.txt", encoding="utf-8").read()
say(llms.startswith("# "), "llms.txt starts with an H1")
say(re.search(r"^> .{80,}", llms, re.M) is not None, "llms.txt has a > summary line")
say("## Pages" in llms, "llms.txt has a ## Pages section")
say(NAME in llms, "llms.txt names %s" % NAME)

print("  => SEO/LLM-SEO: %s" % ("FAIL" if bad else "pass"))
sys.exit(bad)
