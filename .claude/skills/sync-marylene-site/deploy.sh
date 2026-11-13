#!/usr/bin/env bash
# deploy.sh — re-apply ALL deploy-only transforms after pulling the *.dc.html pages
# from Claude Design (via extract-pulled.py), then verify. Idempotent.
#
# Adapted from sync-book-site (itself adapted from gregory-renard-site). Differences:
# seven pages instead of one, EN/FR is an in-page toggle (no /fr URL, no variant page),
# so the book's book-seo.py (fr.html generator) and layout-fix.py (book hero fixes) are
# gone. site-seo.py applies the robots mode, favicons, social image and JSON-LD; slug-links.py
# keeps the deployed URLs identical to the legacy Wix ones. The contact form is not wired
# (see SKILL.md, 'Forms').
#
# Pipeline order is critical (see SKILL.md):
#   cp Home->index -> home-link ./ -> slug-links -> seo-clean-urls -> site-seo -> rename *.dc.html->*.html
#   (+ rm Home) -> bump sitemap -> prerender (LAST) -> verify
#
# Does NOT touch the permanent repo files (404.html, CNAME, robots.txt, sitemap.xml
# content, llms.txt, support.js) — they are not from Design and must survive every sync.
#
# Usage:  bash .claude/skills/sync-marylene-site/deploy.sh      (run from anywhere)
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$SKILL_DIR/../../.." && pwd)"
cd "$REPO"

# Page lists come from pages.json via manifest.py — never re-hardcode them here.
# HOME_SRC is read as a whole line: the Design home filename contains spaces.
HOME_SRC="$(python3 "$SKILL_DIR/manifest.py" home-design)"
SUBPAGES="$(python3 "$SKILL_DIR/manifest.py" subpages | tr '\n' ' ')"
# The home as Design links to it: spaces percent-encoded (e.g. "Marylene%20Delbourg-Delphis%20-%20Home.dc.html")
HOME_URL="$(python3 -c 'import sys,urllib.parse; print(urllib.parse.quote(sys.argv[1]))' "$HOME_SRC")"
HOME_RE="$(printf '%s' "$HOME_URL" | sed 's/[.[\*^$/]/\\&/g')"

[ -f "$HOME_SRC" ] || { echo "ERROR: '$HOME_SRC' not found — run extract-pulled.py first."; exit 1; }

shopt -s nullglob
DC_FILES=( *.dc.html )

echo "==> 1/7  clean root: index.html = home page"
cp "$HOME_SRC" index.html

echo "==> 2/7  rewrite home link -> ./  (href + JS url forms, quote-anchored)"
sed -i '' "s|\"$HOME_RE\"|\"./\"|g" "${DC_FILES[@]}" index.html
sed -i '' "s|'$HOME_RE'|'./'|g"     "${DC_FILES[@]}" index.html

echo "==> 3/7  deployed slugs = legacy Wix URLs (about, book, speaking, more, blog, contact)"
python3 "$SKILL_DIR/slug-links.py"

echo "==> 4/7  clean URLs + static SEO head"
python3 "$SKILL_DIR/seo-clean-urls.py"

echo "==> 5/7  site SEO: robots mode, theme-color, favicons, OG/Twitter image, JSON-LD"
python3 "$SKILL_DIR/site-seo.py"

echo "==> 6/7  rename *.dc.html -> *.html (+ drop redundant home source), bump sitemap <lastmod>"
for f in $SUBPAGES; do [ -f "$f.dc.html" ] && mv "$f.dc.html" "$f.html"; done
rm -f "$HOME_SRC"
TODAY="$(date +%F)"
sed -i '' "s|<lastmod>[^<]*</lastmod>|<lastmod>$TODAY</lastmod>|g" sitemap.xml

echo "==> 7/7  static pre-render (headless): real content for no-JS / non-JS crawlers"
python3 "$SKILL_DIR/prerender.py"

echo
bash "$SKILL_DIR/verify.sh"
