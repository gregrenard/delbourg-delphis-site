#!/usr/bin/env python3
"""Deploy-only transform: robots mode, icons, social image and JSON-LD on every page.

Run from the repo root, AFTER seo-clean-urls.py (the static <head> must already exist)
and BEFORE the *.dc.html -> *.html rename. Idempotent: a marker comment guards the
additive parts, and the robots rewrite is a no-op once applied.

1. Robots mode. Design ships `<meta name="robots" content="index, follow">` on every
   page, in the <helmet> that the runtime also injects at load. While pages.json says
   "draft": true this becomes `noindex, nofollow` in the whole file (static head AND
   helmet, so the runtime cannot re-add `index, follow`), because
   www.delbourg-delphis.org is still Marylene's live Wix site and a draft copy must never
   compete with it in search results. When "draft" is false the Design value is kept.
2. Head extras: theme-color (paper #FBFAF7), favicon and apple-touch-icon (relative paths,
   so they work under a github.io project path too).
3. Social image: every page gets the local 1200x630 card (assets/og-card.jpg: portrait, name,
   tagline) as og:image and twitter:image, served from LIVE_URL. Design's own og:image on the
   Home is the Wix portrait cropped from the top, which previews as a head of hair; on Books
   it is a 454x654 cover with baked-in text. Both are replaced, in the head and the helmet.
4. JSON-LD, built here (Design only ships Person on the Home):
   - WebSite on the Home, declaring inLanguage en + fr;
   - BreadcrumbList on every sub-page;
   - AboutPage / ContactPage / WebPage as the page's own type;
   - Book x2 on /book, only with facts the page itself states (title, author, publisher,
     year, foreword, Amazon links). No ISBN is asserted.

There is no French variant here: each page carries its own EN/FR toggle (localStorage
`mdd_lang`), so there is no per-language <head> to write. The component script and the
Design <helmet> text are never rewritten.
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from manifest import DRAFT, LIVE_URL, PAGES, SITE, home_design  # noqa: E402

HOME_DESIGN = home_design()

import re  # noqa: E402

MARK = 'id="site-seo-ld"'
IMG_TAGS = re.compile(r'[ \t]*<meta (?:property="og:image[^"]*"|name="twitter:image") content="[^"]*">\n?')
INDEX = '<meta name="robots" content="index, follow">'
NOINDEX = '<meta name="robots" content="noindex, nofollow">'
# Absolute, and on the host that actually answers today: in draft that is the github.io preview,
# NOT www.delbourg-delphis.org (still the live Wix site, which has no such file).
OG_IMAGE = LIVE_URL + "/assets/og-card.jpg"
OG_ALT = "Marylene Delbourg-Delphis — Innovation and people in the 21st century"
PERSON = {"@type": "Person", "name": "Marylene Delbourg-Delphis", "url": SITE + "/"}

TYPE = {"about": "AboutPage", "contact": "ContactPage"}
NAME = {"about": "About", "book": "Books", "speaking": "Speaking", "more": "Writings",
        "blog": "Blog", "contact": "Contact"}


def books():
    return [
        {"@context": "https://schema.org", "@type": "Book",
         "name": "Beyond Eureka! The Rocky Roads to Innovating", "inLanguage": "en",
         "author": PERSON, "publisher": {"@type": "Organization", "name": "Georgetown University Press"},
         "datePublished": "2024-06", "url": SITE + "/book",
         "sameAs": ["https://www.amazon.com/Beyond-Eureka-Rocky-Roads-Innovating-ebook/dp/B0CNL4WH81"]},
        {"@context": "https://schema.org", "@type": "Book",
         "name": "Everybody Wants to Love Their Job: Rebuilding Trust and Culture", "inLanguage": "en",
         "author": PERSON, "datePublished": "2018", "url": SITE + "/book",
         "sameAs": ["https://www.amazon.com/Everybody-Wants-Love-Their-Job/dp/235456337X"],
         "workTranslation": {"@type": "Book", "name": "Tout le monde veut aimer son travail", "inLanguage": "fr",
                             "author": PERSON,
                             "sameAs": ["https://www.amazon.fr/Tout-monde-veut-aimer-travail/dp/2354563132"]}},
    ]


def ld_blocks(slug):
    out = []
    if slug == "index":
        out.append({"@context": "https://schema.org", "@type": "WebSite", "name": "Marylene Delbourg-Delphis",
                    "url": SITE + "/", "inLanguage": ["en", "fr"], "author": PERSON})
        return out
    url = "%s/%s" % (SITE, slug)
    out.append({"@context": "https://schema.org", "@type": TYPE.get(slug, "WebPage"), "name": NAME[slug],
                "url": url, "inLanguage": ["en", "fr"], "isPartOf": {"@type": "WebSite", "url": SITE + "/"},
                "about": PERSON})
    out.append({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": NAME[slug], "item": url}]})
    if slug == "book":
        out.extend(books())
    return out


def slug_of(path):
    """index for the Home (its Design source or the generated index.html), else the slug."""
    base = os.path.basename(path)
    if base == "index.html" or base == HOME_DESIGN:
        return "index"
    return base[: -len(".dc.html")]


def meta_present(head, attr, name):
    return ('%s="%s"' % (attr, name)) in head


pages = sorted(glob.glob("*.dc.html")) + (["index.html"] if os.path.exists("index.html") else [])
for p in pages:
    s = open(p, encoding="utf-8").read()
    if MARK not in s.partition("<body")[0]:
        # Design's og:image is the Wix portrait cropped from the top (al_t): social previews
        # show only her hair. One local, designed card replaces it everywhere, helmet included.
        s = IMG_TAGS.sub("", s)
    head, sep, body = s.partition("<body")
    if "<title>" not in head:
        sys.exit("site-seo: %s has no static <title> in <head>; run seo-clean-urls.py first" % p)
    if MARK not in head:
        extra = []
        if 'name="theme-color"' not in head:
            extra.append('<meta name="theme-color" content="#FBFAF7">')
        if 'rel="icon"' not in head:
            extra.append('<link rel="icon" type="image/png" href="assets/favicon.png">')
        if 'rel="apple-touch-icon"' not in head:
            extra.append('<link rel="apple-touch-icon" href="assets/apple-touch-icon.png">')
        extra.append('<meta property="og:image" content="%s">' % OG_IMAGE)
        extra.append('<meta property="og:image:type" content="image/jpeg">')
        extra.append('<meta property="og:image:width" content="1200">')
        extra.append('<meta property="og:image:height" content="630">')
        extra.append('<meta property="og:image:alt" content="%s">' % OG_ALT)
        extra.append('<meta name="twitter:image" content="%s">' % OG_IMAGE)
        for i, block in enumerate(ld_blocks(slug_of(p))):
            tag_id = ' %s' % MARK if i == 0 else ""
            extra.append('<script type="application/ld+json"%s>%s</script>'
                         % (tag_id, json.dumps(block, ensure_ascii=False, separators=(",", ":"))))
        head = head.replace("</head>", "\n".join(extra) + "\n</head>", 1)
    s = head + sep + body
    if DRAFT:
        # Whole file, not just <head>: the <helmet> inside <x-dc> carries the same tag and
        # support.js injects it into <head> at runtime, which would add a contradictory
        # `index, follow` next to the static noindex.
        s = s.replace(INDEX, NOINDEX)
    open(p, "w", encoding="utf-8").write(s)
    print("site-seo: %-44s robots=%s" % (p, "noindex (draft)" if DRAFT else "as Design"))
