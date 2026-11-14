---
name: sync-marylene-site
description: Publish the latest version of Marylene Delbourg-Delphis's website from Claude Design to its GitHub repo — pull, re-apply deploy transforms, check mobile / tablet / desktop layout in English AND French, SEO, LLM-SEO (llms.txt, AI crawlers, JSON-LD), commit, push `main` (standing authorization, only if the blocking gates pass), verify the live site and debrief. Use when the user says "mets à jour le site de Marylène", "synchronise le site de Marylène", "publie le site de Marylène", "sync Marylene's site", "update the Delbourg-Delphis site from Claude Design".
---

# Sync Marylene's site: Claude Design → checks → commit → push (if gates pass) → GitHub → live → debrief

The personal site of **Marylene Delbourg-Delphis** (serial technology CEO, advisor, board member, author of *Beyond Eureka!* and *Everybody Wants to Love Their Job*). It is **not** the book site (`sync-book-site`, `working-with-another-intelligence.com`) and **not** gregory-renard.com. The pipeline is adapted from `sync-book-site`; the differences are listed at the end.

## Project facts
- **Source of truth:** Claude Design project "Delbourg-Delphis website modernization", projectId `5caa756d-b49e-43b0-a47f-5e225e600ee7`. Type `PROJECT_TYPE_PROJECT`, so **DesignSync is read-only**: only `list_files` and `get_file`, never `finalize_plan` / `write_files` / `delete_files`.
- **Pages** (single source of truth: `pages.json`): the Design home becomes `index.html`, plus six content pages. Deployed slugs are the **legacy Wix URLs**: `about`, `book`, `speaking`, `more`, `blog`, `contact`. Design names the files About / Books / Speaking / Writings / Blog / Contact, and `slug-links.py` reconciles the two (see "Why the slugs are lowercase").
- **Languages:** English and French, switched by an in-page toggle (localStorage `mdd_lang`). There is no `/fr` URL and no variant page.
- **Mode:** `pages.json` → `"draft": true`. `www.delbourg-delphis.org` is still Marylene's **live Wix site**, so a draft copy has **no CNAME and every page is noindex**. Launching means `"draft": false`, adding `CNAME` (`www.delbourg-delphis.org`), redeploying and pointing the DNS: that is a decision for Gregory and Marylene, never a side effect of a sync.
- **Repo:** to be created. Suggested `gregrenard/delbourg-delphis-site` (public), branch `main`, GitHub Pages from `main` root. `preview_url` in `pages.json` assumes that name; update both if it changes.
- **gh account:** `gregrenard` (`gh auth switch -u gregrenard` if another is active; leave it on `gregrenard` afterwards). Run `gh auth status | head -3` before any `gh` or `git push`.
- ⚠️ The Design project's `github.md` names `gregory-renard-site` as its target, a leftover. **Never push this site there.**

## Push policy: standing authorization for `main`, nothing else
Gregory gave a standing push authorization for this repo on 2026-11-13, same arrangement as `sync-book-site`: the flow pushes `main` of `gregrenard/delbourg-delphis-site` **when every blocking gate of `verify.sh` passes**, then runs `verify-live.sh` and ends with the debrief. Never push past a failing blocking gate.

The authorization covers `git push origin main` and nothing else. Still needing an explicit go, per action: tags, `gh repo create`, GitHub Pages settings, and launching (`"draft": false`, `CNAME`, DNS, indexing).

## The flow
1. **Structure:** `DesignSync list_files`, then compare the page files with `python3 .claude/skills/sync-marylene-site/manifest.py design`. A new or renamed page means updating `pages.json` (with its legacy slug if it existed on Wix), then `sitemap.xml` and `llms.txt` (gate (i)); flag it in the debrief.
2. **Pull:** `DesignSync get_file` for each page, plus `support.js` (compare with the repo copy, which is identical to the book site's; replace it only if it changed). Files over 256 KiB come back truncated: keep the repo's working file, never commit a truncated one, and list it in the debrief.
3. **Write byte-exact:** `python3 .claude/skills/sync-marylene-site/extract-pulled.py <session.jsonl>`. **Pass the transcript path explicitly** (`~/.claude/projects/-Users-gregoryrenard-Documents-bool-marylene/<session>.jsonl`): the session usually starts in `bool_marylene/`, not in the repo, so auto-discovery looks in the wrong folder. **Never retype a page.**
4. **Deploy + all gates:** `bash .claude/skills/sync-marylene-site/deploy.sh` (transforms, then `verify.sh`: gates a–m, below). About one minute.
5. **Review:** `git diff --stat`, then a text-level diff of the Design pages against the previous pull, to know what the authors changed. It feeds the commit message and the debrief.
6. **Commit** (English, explains what changed and why, with the numbers, **no Claude attribution**). If `verify.sh` has any **BAD**, stop: no commit of the failing state, go to the debrief.
7. **Push** is covered by the standing authorization (see "Push policy"), provided step 4 had no BAD. Without that, stop and go to the debrief.
8. **Push:** `git push origin main` (with `gregrenard`). If rejected: `git -c credential.helper= -c credential.helper='!gh auth git-credential' push origin main`. Then `bash .claude/skills/sync-marylene-site/verify-live.sh`, which waits for the Pages build of this commit and checks HTTP on every page, assets and the 404, plus a headless render of every page.
9. **Debrief** (always, even when stopped early). Write it in French, short, in this order:
   - **Résultat :** committed / pushed or not, commit SHA, live links when pushed.
   - **Ce qui a changé dans Claude Design :** 3–6 bullets from step 5.
   - **Contrôles :** one line per family: layout mobile / tablette / desktop × EN / FR, languages, SEO, LLM-SEO, live, each with ✅ or ❌.
   - **Avertissements :** every WARN, grouped (unwired contact form, hotlinked images, long titles and descriptions).
   - **À faire côté Design / auteurs :** only the actions that belong to them.
   - If it was stopped at a BAD: what failed, why, and the fix.

## Pipeline (deploy.sh) and ordering constraints
```
1  cp "<Home>.dc.html" index.html            clean root, no redirect
2  home-link rewrite -> "./"                 quote-anchored; name read from pages.json, %20-encoded
3  slug-links.py                             Design names -> legacy Wix slugs (links + file rename)
4  seo-clean-urls.py                         strip .dc.html, lift <helmet> into <head>, lang="en"
5  site-seo.py                               robots mode, theme-color, favicons, og/twitter image (one local card for every page), JSON-LD
6  rename *.dc.html -> *.html, rm home source, bump sitemap <lastmod>
7  prerender.py                              LAST: static mirror for no-JS crawlers
   verify.sh                                 gates a–m
```
- Pre-render runs **last**. `slug-links.py` runs **before** clean-URLs (it matches the `.dc.html` form). `site-seo.py` runs **after** clean-URLs (it needs the static `<head>`) and **before** the rename.
- `index.html` and the six content pages are **generated**: never edit them. Fix content in Claude Design.
- The draft `noindex` is applied to the **whole file**, helmet included: support.js injects the helmet into `<head>` at runtime, and an untouched helmet would put `index, follow` next to the static `noindex`.
- `site-seo.py` never rewrites the component script or the helmet text. A French apostrophe inside a JS `'…'` literal broke the book site's runtime on 2026-09-24, so strings stay in Design.

## Verify gates (verify.sh)
| Gate | Checks | Blocking |
|---|---|---|
| (a) | no `.dc.html`, no `.//`, no leftover Design source | yes |
| (b) | index is the home, not a redirect | yes |
| (c) | `<title>` + `og:title` in `<head>` on all 7 pages | yes |
| (d) (d2) | internal links resolve; none still uses a Design-cased name (`About`, `Books`…) | yes |
| (e) | local assets resolve | yes |
| (f) | permanent files and icons present; **draft:** no CNAME and all 7 pages noindex / **launched:** CNAME = domain | yes |
| (h) | pre-render mirror with zero `{{ }}` | yes when launched, **WARN in draft** |
| (i) | `pages.json` = `sitemap.xml` = `llms.txt` (7 URLs) | yes |
| (j) | contact form wired | WARN |
| (k) | each page: static `lang="en"`, own canonical, EN and FR dictionaries, language toggle | yes |
| (l) | **layout** (`check-layout.py`): all 7 pages × **390 / 768 / 1440 px** × **EN and FR** = 42 renders in a true-width iframe: no horizontal scroll, no unclipped element past the edge, `<h1>` rendered, `<html lang>` equals the requested language and the header carries that language's nav label. Visible `{{ }}` = WARN | yes |
| (m) | **SEO + LLM-SEO** (`check-seo.py`): title / description (length = WARN), canonical equals the deployed URL, OG + Twitter tags, og:image local, 1200×630, under 300 KB (hotlinked = WARN), JSON-LD (Person + WebSite on Home, BreadcrumbList on sub-pages, two Book entries on /book), favicon + apple-touch-icon, robots meta matches the mode; robots.txt allows GPTBot, OAI-SearchBot, ClaudeBot, PerplexityBot, Google-Extended; llms.txt well-formed and naming Marylene | yes |

How the two languages are tested: the site has no per-language URL, so the layout gate's server injects `localStorage.setItem('mdd_lang', <lang>)` as the first thing in `<head>`, before `support.js` runs. The runtime then starts in that language exactly as for a returning visitor who chose it.

## Why the slugs are lowercase (`about`, `book`, `more`…)
Design's pages carry canonicals copied from the Wix site: `/about`, `/book`, `/speaking`, `/more` (Writings), `/blog`, `/contact`. The nav links use the Design file names (`About`, `Books`, `Writings`…). GitHub Pages is case-sensitive, so serving `/About` while the canonical says `/about` would split every page in two for search engines and break every inbound link from the Wix era. Deploying under the legacy slugs keeps the canonicals correct as shipped and keeps old links alive on the day the domain moves. Alternative if the authors prefer readable URLs (`/books`, `/writings`): change the slugs in `pages.json`, set matching canonicals in Design, and add redirect stubs (`role: stub`) for the old Wix paths.

## Open items (not for the sync to fix)
- **Book share card:** `/book` uses the same card as every page, because the Wix cover has "June 2024" and "Georgetown University Press" baked into the image and clashes with a designed card. With a clean cover, add `og-book.html` to `assets-src/` and map `book` to it in `site-seo.py`.
- **Contact form** sends nothing (it only sets `sent:true`). Before launch: pick an endpoint (Brevo, or a dedicated Google Apps Script), add honeypot + consent, write `patch-forms.py`, mark `data-form-endpoint=`. **Never reuse another site's endpoint.**
- **Hotlinked images:** the pages load photos and covers from `static.wixstatic.com` (5) and `substackcdn.com` (1), and the Home `og:image` is a Wix URL. They die with the Wix account. Copy them into `assets/` (Design copies over 256 KiB cannot be pulled, so use the originals) before the domain leaves Wix.
- **Titles and descriptions** over the recommended length (book 90 / more 81 chars; most descriptions 180–210): edit in Design, they are WARN only.
- **French URLs:** the toggle serves French only to browsers that run JavaScript and chose it; search engines see English. Giving French its own URLs (`/fr/...`, `hreflang`) is a product decision for Gregory and Marylene, not built.
- **Design `github.md`** still points at `gregory-renard-site`.

## Permanent repo files (not from Design; a sync must never clobber them)
`404.html` (computes its home link, so it works on both hosts), `robots.txt`, `sitemap.xml`, `llms.txt` (hand-written: editorial, never generated), `support.js` (the dc-runtime; vendored), `assets/` (`og-card.jpg`, `favicon.png`, `apple-touch-icon.png`, rendered from `assets-src/*.html` with headless Chrome; the card uses `assets-src/portrait.jpg`), and `CNAME` once launched.

## Differences from sync-book-site
- Seven pages instead of one; `slug-links.py` is new; the book's `book-seo.py` (generates `fr.html`, hardcodes French head strings) and `layout-fix.py` (book hero fixes) are dropped; `site-seo.py` replaces them.
- Gate (k) checks the toggle and dictionaries instead of `/fr` + hreflang; gate (l) adds the language dimension; gate (m) checks Person / WebSite / BreadcrumbList / Book instead of a two-author Book, and does **not** carry the book's hash-based "no real client name" guardrail, which protects that book's client and has no counterpart here.
- Standing push authorization for `main` since 2026-11-13, like the book site, but tags and the launch stay behind an explicit go (see "Push policy").
