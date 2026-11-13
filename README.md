# Marylene Delbourg-Delphis — website

Site of **Marylene Delbourg-Delphis**: serial technology CEO, executive consultant, board member and author of *Beyond Eureka!* and *Everybody Wants to Love Their Job*. A static, bilingual (English / French) site, built for GitHub Pages.

The target domain is **https://www.delbourg-delphis.org**, which today is still her live Wix site. Until the domain is cut over, this repo runs in **draft mode**: no `CNAME`, and every page is `noindex` (`"draft": true` in `.claude/skills/sync-marylene-site/pages.json`).

## How this repo relates to Claude Design

**Claude Design is the source of truth**, not this repo. The pages are authored in the Claude Design project "Delbourg-Delphis website modernization" (projectId `5caa756d-b49e-43b0-a47f-5e225e600ee7`). This repo holds the **deployed output**: the Design pages plus the deploy-only transforms Claude Design cannot express (legacy URLs, static SEO head, JSON-LD, static pre-render for no-JS crawlers).

**Never edit the generated `.html` pages by hand.** The next sync overwrites them. Content changes go in Claude Design; deploy behaviour goes in `.claude/skills/sync-marylene-site/`.

## Updating the site

Run the `sync-marylene-site` skill (`.claude/skills/sync-marylene-site/SKILL.md`), for example « mets à jour le site de Marylène ». It pulls from Claude Design, re-applies every transform, runs the gates and commits. **It then stops and asks for a go before any push**: this repo has no standing push authorization.

The gates check, among others:

- layout on mobile (390 px), tablet (768 px) and desktop (1440 px), in **both English and French**: 7 pages × 3 widths × 2 languages = 42 renders, no horizontal scroll, language really switched;
- SEO: canonicals, Open Graph and Twitter tags, JSON-LD, favicons, robots meta;
- LLM-SEO: `llms.txt`, and `robots.txt` allowing GPTBot, OAI-SearchBot, ClaudeBot, PerplexityBot and Google-Extended;
- consistency: `pages.json`, `sitemap.xml` and `llms.txt` list the same URLs.

## Structure

| File | What it is |
|---|---|
| `index.html`, `about.html`, `book.html`, `speaking.html`, `more.html`, `blog.html`, `contact.html` | Generated: the Design pages, transformed and pre-rendered. The slugs are the legacy Wix URLs (`more` is the Writings page) |
| `support.js` | The Claude Design runtime (vendored, generated, never edit) |
| `assets/` | Social card (1200×630), favicon, apple-touch icon. Rendered from `.claude/skills/sync-marylene-site/assets-src/` |
| `robots.txt`, `sitemap.xml`, `llms.txt`, `404.html` | Repo-only files; a sync must never clobber them. `llms.txt` is hand-written |
| `.claude/skills/sync-marylene-site/` | The sync pipeline: `pages.json` (the only page list), `deploy.sh`, `verify.sh` (gates a–m), `check-layout.py`, `check-seo.py`, `verify-live.sh`… |

## Before launch

- **The contact form sends nothing yet** (verify gate (j)). See `SKILL.md` → "Open items".
- **Images are hotlinked** from Wix and Substack; copy them into `assets/` before leaving Wix.
- **The domain is live on Wix.** Do not add a `CNAME` until the cut-over is decided.

## Preview locally

```
python3 -m http.server 8765    # then open http://localhost:8765/
```

The runtime needs HTTP, not `file://`.
