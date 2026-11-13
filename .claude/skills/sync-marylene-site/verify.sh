#!/usr/bin/env bash
# verify.sh — post-deploy sanity checks. Exits non-zero if anything is wrong.
# Safe to run standalone:  bash .claude/skills/sync-marylene-site/verify.sh
# Adapted from sync-book-site: seven pages, EN/FR as an in-page toggle (gate (k) checks the
# toggle and the French dictionary instead of a /fr URL), one contact form (gate (j)), and
# gate (l) measures every page at 390 / 768 / 1440 px in both languages.
set -uo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$SKILL_DIR/../../.." && pwd)"
cd "$REPO"

SUBPAGES="$(python3 "$SKILL_DIR/manifest.py" subpages | tr '\n' ' ')"
CONTENT="$(python3 "$SKILL_DIR/manifest.py" content  | tr '\n' ' ')"
STUBS="$(python3   "$SKILL_DIR/manifest.py" stubs    | tr '\n' ' ')"
PAGES_HTML="index.html $(for n in $CONTENT; do echo "$n.html"; done | tr '\n' ' ')"
SITE_URL="$(python3 -c "import sys; sys.path.insert(0,'$SKILL_DIR'); from manifest import SITE; print(SITE)")"
SITE_HOST="${SITE_URL#*//}"
DRAFT="$(python3 "$SKILL_DIR/manifest.py" draft)"
fail=0

echo "--- (a) extension gone + no accidental .// ---"
if grep -l "\.dc\.html" *.html >/dev/null 2>&1; then echo "  BAD: .dc.html still present"; fail=1; else echo "  ok: extensionless"; fi
if grep -n '\.//' *.html >/dev/null 2>&1;        then echo "  BAD: .// found";            fail=1; else echo "  ok: no .//"; fi
ls *.dc.html >/dev/null 2>&1 && { echo "  BAD: leftover Design source files: $(ls *.dc.html | tr '\n' ' ')"; fail=1; }

echo "--- (b) index.html is the homepage (not a redirect) ---"
[ "$(grep -c 'http-equiv="refresh"' index.html)" = "0" ] && echo "  ok: no refresh redirect" || { echo "  BAD: index has refresh"; fail=1; }
[ "$(grep -c '<x-dc>' index.html)" -ge 1 ]               && echo "  ok: <x-dc> present"      || { echo "  BAD: no <x-dc>"; fail=1; }

echo "--- (c) static SEO present: each page has <title> + og:title inside <head> ---"
cfail=0
for f in $PAGES_HTML; do
  [ -f "$f" ] || { echo "  MISS page: $f"; fail=1; cfail=1; continue; }
  h=$(awk 'BEGIN{p=1}/<body/{p=0}{if(p)print}' "$f")
  if echo "$h" | grep -q "<title>" && echo "$h" | grep -q "og:title"; then :; else echo "  MISS seo-head: $f"; fail=1; cfail=1; fi
done
[ $cfail -eq 0 ] && echo "  ok: all pages have <title> + og:title in <head>"
echo "--- (c2) redirect stubs carry a refresh + canonical ---"
for n in $STUBS; do
  [ -f "$n.html" ] || continue
  if grep -q 'http-equiv="refresh"' "$n.html" && grep -q 'rel="canonical"' "$n.html"; then echo "  ok: $n redirect stub"; else echo "  WARN: $n missing refresh/canonical"; fi
done
[ -z "$STUBS" ] && echo "  ok: no redirect stubs"

echo "--- (d) every internal page link resolves to a .html file ---"
for n in $SUBPAGES; do
  if grep -qhoE "href=\"$n\"|url: '$n'" *.html 2>/dev/null; then
    [ -f "$n.html" ] && echo "  ok: $n" || { echo "  MISS: $n.html"; fail=1; }
  else
    echo "  BAD: no page links to /$n (nav link rewritten wrongly?)"; fail=1
  fi
done
echo "--- (d2) no link still points at a Design-cased name (About, Books, Writings…) ---"
if grep -qhE 'href="(About|Books|Speaking|Writings|Blog|Contact)"' *.html 2>/dev/null; then
  echo "  BAD: Design-cased internal link found; it would 404 on the case-sensitive host"; fail=1
else echo "  ok: all internal links use the deployed slugs"; fi

echo "--- (e) every local asset reference resolves ---"
for t in $(grep -hoE "assets/[A-Za-z0-9%@_./-]+\.(png|jpg|jpeg|webp|gif|svg|mp4|mp3|pdf)" *.html 2>/dev/null | sort -u); do
  [ -f "$t" ] && echo "  ok: $t" || { echo "  MISS: $t"; fail=1; }
done

echo "--- (f) permanent repo files intact (must NOT be clobbered by a sync) ---"
for pf in 404.html robots.txt sitemap.xml llms.txt support.js assets/og-card.jpg assets/favicon.png assets/apple-touch-icon.png; do
  [ -f "$pf" ] && echo "  ok: $pf" || { echo "  BAD: $pf MISSING"; fail=1; }
done
if [ "$DRAFT" = "1" ]; then
  [ -f CNAME ] && { echo "  BAD: draft phase but CNAME present (it would hijack the live Wix domain)"; fail=1; } || echo "  ok: draft phase, no CNAME"
  for f in $PAGES_HTML; do
    grep -q '<meta name="robots" content="noindex, nofollow">' "$f" && ! grep -q 'content="index, follow"' "$f" \
      && echo "  ok: $f is noindex (draft)" || { echo "  BAD: $f not noindex in draft phase"; fail=1; }
  done
else
  [ "$(tr -d '[:space:]' < CNAME 2>/dev/null)" = "$SITE_HOST" ] && echo "  ok: CNAME = $SITE_HOST" || { echo "  BAD: CNAME does not match pages.json site ($SITE_HOST)"; fail=1; }
fi
grep -q "Sitemap: $SITE_URL/sitemap.xml" robots.txt && echo "  ok: robots.txt Sitemap line" || { echo "  BAD: robots.txt Sitemap line wrong"; fail=1; }

echo "--- (h) static pre-render mirror present + resolved (no {{ }} inside it) ---"
for f in $PAGES_HTML; do
  python3 - "$f" "$DRAFT" <<'PY' || fail=1
import sys, re
f = sys.argv[1]; s = open(f, encoding="utf-8").read()
m = re.search(r"<!--dc-prerender-start-->(.*?)<!--dc-prerender-end-->", s, re.S)
if not m:
    if sys.argv[2] == "1":
        # Draft phase: pages are noindex, so the no-JS mirror is not needed yet. The usual
        # cause is an unfilled {{ }} placeholder in Design (check-layout reports it).
        print("  WARN (draft, non-blocking): no pre-render mirror:", f); sys.exit(0)
    print("  MISS pre-render mirror:", f); sys.exit(1)
if 'id="dc-prerender-css"' not in s:
    print("  MISS swap CSS:", f); sys.exit(1)
ph = len(re.findall(r"\{\{[^}]*\}\}", m.group(1)))
if ph:
    print("  BAD: %d unresolved {{ }} inside mirror: %s" % (ph, f)); sys.exit(1)
print("  ok:", f)
PY
done

echo "--- (k) languages: EN static, French dictionary + working toggle on every page ---"
python3 - $PAGES_HTML <<'PYK' || fail=1
import re, sys
bad = 0
for f in sys.argv[1:]:
    try:
        s = open(f, encoding="utf-8").read()
    except FileNotFoundError:
        print("  BAD: %s missing" % f); bad = 1; continue
    head = s.split("<body", 1)[0]
    checks = {
        'static <html lang="en">': '<html lang="en">' in s,
        "own canonical": bool(re.search(r'rel="canonical" href="https?://[^"]+"', head)),
        "FR dictionary (fr: {)": bool(re.search(r"\bfr:\s*\{", s)),
        "EN dictionary (en: {)": bool(re.search(r"\ben:\s*\{", s)),
        "language toggle (toggleLang + persisted mdd_lang)": "toggleLang" in s and "mdd_lang" in s,
    }
    miss = [k for k, v in checks.items() if not v]
    print(("  ok: " if not miss else "  BAD: ") + f + (" (lang en, canonical, EN+FR dictionaries, toggle)" if not miss else " missing: " + ", ".join(miss)))
    bad |= bool(miss)
sys.exit(bad)
PYK
echo "    (the rendered FR/EN switch itself is exercised in gate (l))"

echo "--- (i) pages.json == sitemap.xml == llms.txt (three-way, both directions) ---"
python3 - "$SKILL_DIR" <<'PY2' || fail=1
import re, sys
sys.path.insert(0, sys.argv[1])
from manifest import sitemap_urls, SITE

def norm(u):
    u = u.split("#")[0].split("?")[0].rstrip("/")
    return u if u else SITE

want = {norm(u) for u in sitemap_urls()}
sm = {norm(m) for m in re.findall(r"<loc>([^<]+)</loc>", open("sitemap.xml", encoding="utf-8").read())}
txt = open("llms.txt", encoding="utf-8").read()
m = re.search(r"^## Pages\s*$(.*?)(?=^## |\Z)", txt, re.S | re.M)
if not m:
    print("  BAD: llms.txt has no '## Pages' section"); sys.exit(1)
ll = {norm(u) for u in re.findall(r"\]\((" + re.escape(SITE) + r"[^)]*)\)", m.group(1))}
bad = 0
for label, got in (("sitemap.xml", sm), ("llms.txt", ll)):
    for u in sorted(want - got):
        print("  BAD: in pages.json but missing from %s: %s" % (label, u)); bad = 1
    for u in sorted(got - want):
        print("  BAD: in %s but not a content page in pages.json: %s" % (label, u)); bad = 1
if bad:
    sys.exit(1)
print("  ok: pages.json, sitemap.xml and llms.txt agree on the same %d URLs" % len(want))
PY2

echo "--- (j) contact form wired to a real endpoint (WARN until the endpoint exists) ---"
if grep -q 'data-form-endpoint=' contact.html 2>/dev/null; then
  echo "  ok: contact form wired"
else
  echo "  WARN: the contact form shows a success state but sends nothing (onSubmit only sets"
  echo "        sent:true). Wire a dedicated endpoint for THIS site before launch (see SKILL.md)."
fi

echo "--- (l) layout: mobile 390 / tablet 768 / desktop 1440 x EN + FR, no overflow ---"
python3 "$SKILL_DIR/check-layout.py" || fail=1

echo "--- (m) SEO + LLM-SEO ---"
python3 "$SKILL_DIR/check-seo.py" || fail=1

echo
[ $fail -eq 0 ] && echo "VERIFY: all checks passed ✅" || echo "VERIFY: FAILURES above ❌"
exit $fail
