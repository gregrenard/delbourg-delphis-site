#!/usr/bin/env python3
"""Deploy-only transform: content additions that Claude Design does not hold yet.

Added after Marylene's session with Gregory on 2026-11-13. Small and additive on purpose: she likes the
site as it is, so nothing is redesigned. Every change is a data or markup addition inside the Design
component, re-applied after each pull, idempotent (marker `mdd-enrich`), and it fails loudly if an anchor
disappears (a Design change moved the text): fix the anchor here, never skip silently.

1. Axiom: the "2026 Axiom Book Awards, Silver Medal" medal (assets/axiom-silver-medal-2026.png) as an award band
   on the home and the books page, and a 2026 milestone on the About timeline.
2. Beyond Eureka!: the five back-cover endorsements (Solis, Yeh, Rives, Bayen, Mitra) on the books page and in the
   home praise list, EN and FR.
3. Legion of Honour: named "Knight of the Legion of Honour" / "Chevalier de la Légion d'honneur" in the home hero
   line, the recognition strip and the About timeline. Text only: no image of the decoration.

Run BEFORE prerender.py (the static mirror is regenerated from the result).
"""
import os, re, sys
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
MARK = "mdd-enrich"

def rd(p): return open(p, encoding="utf-8").read()
def wr(p, s): open(p, "w", encoding="utf-8").write(s)
def must(s, old, new, label, count=1):
    if old not in s:
        sys.exit("enrich-content: ANCHOR NOT FOUND (%s). A Design change moved it: update the anchor in enrich-content.py." % label)
    return s.replace(old, new, count)
def js(s): return s.replace("\\", "\\\\").replace("'", "\\'")

AX = {
 "en": dict(kicker="Award", title="Silver Medal, 2026 Axiom Book Awards",
            text="Beyond Eureka! The Rocky Roads to Innovating received a Silver Medal at the 2026 Axiom Book Awards.",
            alt="2026 Axiom Book Awards, Silver Medal Winner"),
 "fr": dict(kicker="Distinction", title="Médaille d’argent, Axiom Book Awards 2026",
            text="Beyond Eureka! The Rocky Roads to Innovating reçoit la médaille d’argent des Axiom Book Awards 2026.",
            alt="Axiom Book Awards 2026, médaille d’argent"),
}
Q = {
 "en": [
  ("Provides a treasure trove of best-in-class mindsets and approaches to ideation and creation.", "Brian Solis", "Futurist, innovator, and best-selling author"),
  ("Brings the concept of ‘innovation kairos’ to everyone from venture capitalists to inventors.", "Chris Yeh", "General partner, Blitzscaling Ventures, and co-author of Blitzscaling"),
  ("A must for entrepreneurs and intrapreneurs who want to learn from Silicon Valley’s biggest successes and failures.", "Eugenie Rives", "General manager at X, Alphabet’s Moonshot Factory"),
  ("A thought-provoking academic journey that will undoubtedly inspire readers to reconsider standard approaches.", "Alexandre Bayen", "Associate provost and professor of electrical engineering and computer sciences, UC Berkeley"),
  ("A profoundly original thinker, Marylene offers deep insights on the why, how, who, and where of innovation.", "Sramana Mitra", "Founder and CEO, One Million by One Million (1Mby1M)"),
 ],
 "fr": [
  ("Un trésor de mentalités et d’approches de premier ordre pour imaginer et créer.", "Brian Solis", "Futuriste, innovateur et auteur de best-sellers"),
  ("Fait découvrir le concept de « kairos de l’innovation » à tous, des investisseurs en capital-risque aux inventeurs.", "Chris Yeh", "Associé général de Blitzscaling Ventures et coauteur de Blitzscaling"),
  ("Une lecture indispensable pour les entrepreneurs et les intrapreneurs qui veulent apprendre des plus grands succès et échecs de la Silicon Valley.", "Eugenie Rives", "General manager at X, la Moonshot Factory d’Alphabet"),
  ("Un parcours intellectuel stimulant qui inspirera sans aucun doute les lecteurs à repenser les approches habituelles.", "Alexandre Bayen", "Vice-recteur délégué et professeur de génie électrique et d’informatique, UC Berkeley"),
  ("Une penseuse profondément originale : Marylene offre des éclairages précieux sur le pourquoi, le comment, le qui et le où de l’innovation.", "Sramana Mitra", "Founder and CEO, One Million by One Million (1Mby1M)"),
 ],
}
MORE = {"en": "More praise for Beyond Eureka!", "fr": "Autres avis sur Beyond Eureka!"}

def band(extra=""):
    return ('<section class="mdd-pad" data-screen-label="Award" data-%s="1" style="max-width:1240px;margin:0 auto;padding:40px 36px 0">'
            '<div style="display:flex;gap:28px;align-items:center;border-bottom:1px solid var(--line-soft);padding-bottom:36px">'
            '<img src="assets/axiom-silver-medal-2026.png" alt="{{ t.axiomAlt }}" loading="lazy" width="140" height="173" style="width:140px;height:auto;display:block;border-radius:4px;flex:none">'
            '<span style="display:block;min-width:0">'
            '<span style="display:block;font-size:11px;letter-spacing:0.18em;text-transform:uppercase;font-weight:600;color:var(--red)">{{ t.axiomKicker }}</span>'
            '<span style="display:block;margin-top:10px;font-family:var(--font-display);font-size:clamp(24px,2.6vw,36px);line-height:1.1;letter-spacing:-0.01em;font-weight:500">{{ t.axiomTitle }}</span>'
            '<span style="display:block;margin-top:10px;font-size:16px;line-height:1.55;color:var(--ink-soft);max-width:640px;text-wrap:pretty">{{ t.axiomText }}</span>'
            '</span></div></section>\n\n  ') % MARK

def ax_keys(lang):
    a = AX[lang]
    return "axiomKicker: '%s', axiomTitle: '%s', axiomText: '%s', axiomAlt: '%s',\n        " % (js(a["kicker"]), js(a["title"]), js(a["text"]), js(a["alt"]))

def quote_items(lang, with_book):
    out = []
    for q, n, r in Q[lang]:
        b = "book: 'Beyond Eureka!', " if with_book else ""
        out.append("          { %squote: '%s', name: '%s', role: '%s' }" % (b, js(q), js(n), js(r)))
    return ",\n".join(out)

def insert_after_list_start(s, key, lang_idx_marker, items):
    """Append `items` to the JS array that starts at the `lang_idx_marker`-th occurrence of `key` (0=en, 1=fr)."""
    idx = -1
    for _ in range(lang_idx_marker + 1):
        idx = s.index(key, idx + 1)
    end = s.index("\n        ],", idx)
    return s[:end] + ",\n" + items + s[end:]

# ---------- index.html ----------
p = "index.html"; s = rd(p)
if MARK not in s:
    s = must(s, 'heroCreds: \'Legion of Honour 2018 · École normale supérieure',
             ax_keys("en") + 'heroCreds: \'Knight of the Legion of Honour 2018 · 2026 Axiom Book Awards Silver Medal · École normale supérieure', "home hero en")
    s = must(s, 'heroCreds: \'Légion d’honneur 2018 · École normale supérieure',
             ax_keys("fr") + 'heroCreds: \'Chevalier de la Légion d’honneur 2018 · Axiom Book Awards 2026, médaille d’argent · École normale supérieure', "home hero fr")
    s = insert_after_list_start(s, "praise: [", 0, quote_items("en", True))
    s = insert_after_list_start(s, "praise: [", 1, quote_items("fr", True))
    s = must(s, "{ l: 'Légion d’honneur', s: 'France’s highest order of merit · 2018' }", "{ l: 'Knight of the Legion of Honour', s: 'France’s highest order of merit · 2018' }", "recog en")
    s = must(s, "{ l: 'Légion d’honneur', s: 'Plus haute distinction française · 2018' }", "{ l: 'Chevalier de la Légion d’honneur', s: 'Plus haute distinction française · 2018' }", "recog fr")
    s = must(s, "{ n: '2018', l: 'Awarded the French Legion of Honour' }", "{ n: '2018', l: 'Knight of the French Legion of Honour' }", "fact en")
    s = must(s, "{ n: '2018', l: 'Reçoit la Légion d’honneur' }", "{ n: '2018', l: 'Chevalier de la Légion d’honneur' }", "fact fr")
    s = must(s, '<section class="mdd-pad" data-screen-label="Praise"', band() + '<section class="mdd-pad" data-screen-label="Praise"', "home praise section")
    wr(p, s)

# ---------- book.html ----------
p = "book.html"; s = rd(p)
if MARK not in s:
    s = must(s, "kicker: 'Books', title:", ax_keys("en") + "moreKicker: '%s',\n        kicker: 'Books', title:" % js(MORE["en"]), "book kicker en")
    s = must(s, "kicker: 'Livres', title:", ax_keys("fr") + "moreKicker: '%s',\n        kicker: 'Livres', title:" % js(MORE["fr"]), "book kicker fr")
    s = must(s, "        be: {\n          meta: 'Georgetown University Press · June 2024", "        be: {\n          quotes: [\n%s\n          ],\n          meta: 'Georgetown University Press · June 2024" % quote_items("en", False), "be en")
    s = must(s, "        be: {\n          meta: 'Georgetown University Press · juin 2024", "        be: {\n          quotes: [\n%s\n          ],\n          meta: 'Georgetown University Press · juin 2024" % quote_items("fr", False), "be fr")
    s = must(s, "      ewQuotes: t.ew.quotes,", "      ewQuotes: t.ew.quotes, beQuotes: t.be.quotes,", "return")
    fig = re.search(r'(<figure style="margin:40px 0 0;padding:28px 0 0;border-top:1px solid var\(--ink\)">\s*<blockquote[^>]*>“\{\{ t\.be\.quote \}\}”</blockquote>.*?</figure>)', s, re.S)
    if not fig: sys.exit("enrich-content: ANCHOR NOT FOUND (book Mauborgne figure)")
    more = ('\n        <div data-%s="1" style="margin-top:36px"><span style="display:block;font-size:11px;letter-spacing:0.18em;text-transform:uppercase;font-weight:600;color:var(--red)">{{ t.moreKicker }}</span>'
            '<sc-for list="{{ beQuotes }}" as="q" hint-placeholder-count="5"><figure style="margin:0;padding:22px 0;border-bottom:1px solid var(--line-soft)">'
            '<blockquote style="font-size:18px;line-height:1.45;font-style:italic;font-weight:400;text-wrap:pretty">“{{ q.quote }}”</blockquote>'
            '<figcaption style="margin-top:12px"><span style="font-weight:700;font-size:14px">{{ q.name }}</span><span style="display:block;margin-top:3px;font-size:13px;line-height:1.45;color:var(--ink-mute)">{{ q.role }}</span></figcaption>'
            '</figure></sc-for></div>') % MARK
    s = s[:fig.end()] + more + s[fig.end():]
    s = must(s, '<section id="everybody"', band() + '<section id="everybody"', "book everybody section")
    wr(p, s)

# ---------- about.html ----------
p = "about.html"; s = rd(p)
if MARK not in s:
    s = must(s, "{ y: '2018', h: 'Legion of Honour', d: 'France’s highest order of merit for military and civil accomplishments.' },",
             "{ y: '2018', h: 'Knight of the Legion of Honour', d: 'France’s highest order of merit for military and civil accomplishments.' },\n          { y: '2026', h: 'Axiom Book Awards, Silver Medal', d: 'For Beyond Eureka! The Rocky Roads to Innovating.' }, /* mdd-enrich */", "about en")
    s = must(s, "{ y: '2018', h: 'Légion d’honneur', d: 'La plus haute distinction honorifique française, civile et militaire.' },",
             "{ y: '2018', h: 'Chevalier de la Légion d’honneur', d: 'La plus haute distinction honorifique française, civile et militaire.' },\n          { y: '2026', h: 'Axiom Book Awards, médaille d’argent', d: 'Pour Beyond Eureka! The Rocky Roads to Innovating.' }, /* mdd-enrich */", "about fr")
    wr(p, s)
print("enrich-content: index.html, book.html, about.html enriched (Axiom band, 5 endorsements, Legion of Honour wording)")
