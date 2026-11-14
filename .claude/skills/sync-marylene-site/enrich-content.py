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
3. New book: "Working with Another Intelligence" (with Gregory Renard), a banner at the very top of the home and above
   the first book on the books page, linking to its own site (https://working-with-another-intelligence.com), with the
   cover card copied from that site's assets (assets/book-working-with-another-intelligence.png).
4. Watch and listen: her TEDx Palo Alto talk, the Silicon Carne (Carlos Diaz) videos, podcasts and interviews found online,
   as a full list on the Speaking page and the first four on the home (each links to the original page; sources and
   dates are in .works/media-appearances-2026-11-13.md).
5. Legion of Honour: named "Knight of the Legion of Honour" / "Chevalier de la Légion d'honneur" in the home hero
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
# ---------- new book: Working with Another Intelligence ----------
WAI = {
 "en": dict(kicker="New book", title="Working with Another Intelligence", sub="Why AI success depends more on people than technology",
            meta="By Marylene Delbourg-Delphis and Gregory Renard · Foreword by Guy Kawasaki · Ebook and audiobook, English and French · Out 16 December 2026",
            cta="Discover the book and reserve your copy", url="https://working-with-another-intelligence.com/", alt="Working with Another Intelligence, by Marylene Delbourg-Delphis and Gregory Renard"),
 "fr": dict(kicker="Nouveau livre", title="Travailler avec une autre intelligence", sub="L’IA à l’épreuve du réel",
            meta="De Marylène Delbourg-Delphis et Gregory Renard · Préface de Guy Kawasaki · Ebook et livre audio, en français et en anglais · Sortie le 16 décembre 2026",
            cta="Découvrir le livre et réserver votre exemplaire", url="https://working-with-another-intelligence.com/fr", alt="Travailler avec une autre intelligence, de Marylène Delbourg-Delphis et Gregory Renard"),
}
WAIM = "mdd-wai"
def wai_keys(lang):
    w = WAI[lang]
    return "".join("wai%s: '%s', " % (k.capitalize(), js(w[k])) for k in ("kicker", "title", "sub", "meta", "cta", "url", "alt")) + "\n        "
def wai_band(top):
    pad = "28px 36px 0" if top else "40px 36px 0"
    return ('<section class="mdd-pad" data-screen-label="New book" data-%s="1" style="max-width:1240px;margin:0 auto;padding:%s">'
            '<a href="{{ t.waiUrl }}" target="_blank" rel="noopener noreferrer" style="display:flex;flex-wrap:wrap;gap:28px 36px;align-items:center;padding:24px;background:var(--paper-2);border-top:2px solid var(--red);color:var(--ink)">'
            '<img src="assets/book-working-with-another-intelligence.png" alt="{{ t.waiAlt }}" loading="lazy" width="320" height="168" style="width:min(320px,100%%);height:auto;display:block;border-radius:2px;box-shadow:0 18px 40px rgba(20,20,24,0.18);flex:none">'
            '<span style="display:block;flex:1 1 320px;min-width:0">'
            '<span style="display:block;font-size:11px;letter-spacing:0.18em;text-transform:uppercase;font-weight:600;color:var(--red)">{{ t.waiKicker }}</span>'
            '<span style="display:block;margin-top:10px;font-family:var(--font-display);font-size:clamp(28px,3vw,42px);line-height:1.05;letter-spacing:-0.015em;font-weight:500">{{ t.waiTitle }}</span>'
            '<span style="display:block;margin-top:6px;font-family:var(--font-display);font-style:italic;font-size:clamp(18px,1.7vw,23px);color:var(--ink-mute)">{{ t.waiSub }}</span>'
            '<span style="display:block;margin-top:12px;font-size:14px;line-height:1.55;color:var(--ink-soft);max-width:640px;text-wrap:pretty">{{ t.waiMeta }}</span>'
            '<span style="display:inline-block;margin-top:16px;font-size:13.5px;font-weight:600;border-bottom:1px solid var(--red);padding-bottom:1px">{{ t.waiCta }} ↗</span>'
            '</span></a></section>\n\n  ') % (WAIM, pad)

p = "index.html"; s = rd(p)
if WAIM not in s:
    s = must(s, "axiomKicker: 'Award', ", wai_keys("en") + "axiomKicker: 'Award', ", "wai home en")
    s = must(s, "axiomKicker: 'Distinction', ", wai_keys("fr") + "axiomKicker: 'Distinction', ", "wai home fr")
    s = must(s, '<section class="mdd-hero mdd-pad" data-screen-label="Hero"', wai_band(True) + '<section class="mdd-hero mdd-pad" data-screen-label="Hero"', "wai home hero")
    wr(p, s)
p = "book.html"; s = rd(p)
if WAIM not in s:
    s = must(s, "axiomKicker: 'Award', ", wai_keys("en") + "axiomKicker: 'Award', ", "wai book en")
    s = must(s, "axiomKicker: 'Distinction', ", wai_keys("fr") + "axiomKicker: 'Distinction', ", "wai book fr")
    s = must(s, '<section id="beyond-eureka"', wai_band(False) + '<section id="beyond-eureka"', "wai book beyond-eureka")
    wr(p, s)

# ---------- watch and listen ----------
MEDIA = {
 "en": [
  ("Video", "Comment une philosophe française a conquis la Silicon Valley !", "Silicon Carne, Carlos Diaz · YouTube", "https://www.youtube.com/watch?v=41Ow6rlMISQ"),
  ("Video", "What makes a successful trailblazer?", "TEDx Palo Alto · October 2024", "https://www.youtube.com/watch?v=Bx3rVu-6bL8"),
  ("Podcast", "A Pioneer’s Perspective on the Innovation Journey", "Guy Kawasaki’s Remarkable People · May 2024", "https://podcasts.apple.com/us/podcast/maryl%C3%A8ne-delbourg-delphis-a-pioneers-perspective-on/id1483081827?i=1000654155209"),
  ("Podcast", "Empowering Innovation", "Innovator Café, David R. Stevens · October 2024", "https://www.podpage.com/innovator-cafe-with-david-r-stevens/empowering-innovation-a-conversation-with-marylene-delbourg-delphis/"),
  ("Video", "Marylène Delbourg, la trailblazer", "Silicon Carne, Carlos Diaz · YouTube", "https://www.youtube.com/watch?v=TbE_Efbijnw"),
  ("Podcast", "Beyond Eureka! The Rocky Roads to Innovating", "Maker’s Wave · May 2024", "https://www.makerswave.com/beyond-eureka-the-rocky-roads-to-innovating-with-marylene-delbourg-delphis/"),
  ("Podcast", "Faut-il lever pour réussir ?", "Silicon Carne · April 2021", "https://www.frenchweb.fr/silicon-carne-faut-il-lever-pour-reussir/419688"),
  ("Interview", "Meeting with Marylene Delbourg-Delphis, serial entrepreneur in Silicon Valley", "MerciSF, via French Tech SF · May 2024", "https://frenchtechsf.org/news/meeting-with-marylene-delbourg-delphis-serial-entrepreneur-in-silicon-valley/"),
  ("Interview", "Interview Series: Marylene Delbourg-Delphis", "The Delivery Man · June 2024", "https://thedeliveryman.substack.com/p/interview-series-marylene-delbourg"),
 ],
 "fr": [
  ("Vidéo", "Comment une philosophe française a conquis la Silicon Valley !", "Silicon Carne, Carlos Diaz · YouTube", "https://www.youtube.com/watch?v=41Ow6rlMISQ"),
  ("Vidéo", "What makes a successful trailblazer?", "TEDx Palo Alto · octobre 2024", "https://www.youtube.com/watch?v=Bx3rVu-6bL8"),
  ("Podcast", "A Pioneer’s Perspective on the Innovation Journey", "Remarkable People de Guy Kawasaki · mai 2024", "https://podcasts.apple.com/us/podcast/maryl%C3%A8ne-delbourg-delphis-a-pioneers-perspective-on/id1483081827?i=1000654155209"),
  ("Podcast", "Empowering Innovation", "Innovator Café, David R. Stevens · octobre 2024", "https://www.podpage.com/innovator-cafe-with-david-r-stevens/empowering-innovation-a-conversation-with-marylene-delbourg-delphis/"),
  ("Vidéo", "Marylène Delbourg, la trailblazer", "Silicon Carne, Carlos Diaz · YouTube", "https://www.youtube.com/watch?v=TbE_Efbijnw"),
  ("Podcast", "Beyond Eureka! The Rocky Roads to Innovating", "Maker’s Wave · mai 2024", "https://www.makerswave.com/beyond-eureka-the-rocky-roads-to-innovating-with-marylene-delbourg-delphis/"),
  ("Podcast", "Faut-il lever pour réussir ?", "Silicon Carne · avril 2021", "https://www.frenchweb.fr/silicon-carne-faut-il-lever-pour-reussir/419688"),
  ("Entretien", "Meeting with Marylene Delbourg-Delphis, serial entrepreneur in Silicon Valley", "MerciSF, via French Tech SF · mai 2024", "https://frenchtechsf.org/news/meeting-with-marylene-delbourg-delphis-serial-entrepreneur-in-silicon-valley/"),
  ("Entretien", "Interview Series: Marylene Delbourg-Delphis", "The Delivery Man · juin 2024", "https://thedeliveryman.substack.com/p/interview-series-marylene-delbourg"),
 ],
}
MEDIAT = {"en": ("Watch and listen", "Talks, podcasts and interviews", "All talks and interviews"),
          "fr": ("Voir et écouter", "Conférences, podcasts et entretiens", "Toutes les conférences et entretiens")}
MM = "mdd-media"
def media_keys(lang):
    items = ",\n".join("          { k: '%s', t: '%s', s: '%s', u: '%s' }" % tuple(js(x) for x in it) for it in MEDIA[lang])
    k, t, a = MEDIAT[lang]
    return "mediaKicker: '%s', mediaTitle: '%s', mediaAll: '%s',\n        media: [\n%s\n        ],\n        " % (js(k), js(t), js(a), items)
def media_band(listname, all_link):
    link = ('<a href="speaking" style="display:inline-block;margin-top:22px;font-size:13.5px;font-weight:600;color:var(--ink);border-bottom:1px solid var(--red);padding-bottom:1px">{{ t.mediaAll }} →</a>' if all_link else "")
    return ('<section class="mdd-pad" data-screen-label="Watch and listen" data-%s="1" style="max-width:1240px;margin:0 auto;padding:56px 36px 0">'
            '<div style="border-top:1px solid var(--ink);padding-top:14px;display:flex;justify-content:space-between;gap:16px;align-items:baseline">'
            '<span style="font-size:11.5px;letter-spacing:0.22em;text-transform:uppercase;font-weight:600;color:var(--red)">{{ t.mediaKicker }}</span></div>'
            '<h2 style="margin-top:26px;font-size:clamp(26px,3vw,40px);line-height:1.1;letter-spacing:-0.015em;max-width:900px;text-wrap:balance">{{ t.mediaTitle }}</h2>'
            '<div style="margin-top:12px"><sc-for list="{{ %s }}" as="m" hint-placeholder-count="4">'
            '<a href="{{ m.u }}" target="_blank" rel="noopener noreferrer" class="mdd-row" style="display:block;padding:18px 0;border-bottom:1px solid var(--line-soft);color:var(--ink)" style-hover="color:var(--ink)">'
            '<span style="display:block;font-size:11px;letter-spacing:0.18em;text-transform:uppercase;font-weight:600;color:var(--red)">{{ m.k }}</span>'
            '<span style="display:block;margin-top:6px;font-family:var(--font-display);font-size:clamp(20px,2vw,26px);line-height:1.2;font-weight:500;text-wrap:balance">{{ m.t }} ↗</span>'
            '<span style="display:block;margin-top:4px;font-size:13.5px;color:var(--ink-mute)">{{ m.s }}</span></a></sc-for></div>%s</section>\n\n  ') % (MM, listname, link)

p = "index.html"; s = rd(p)
if MM not in s:
    s = must(s, "axiomKicker: 'Award', ", media_keys("en") + "axiomKicker: 'Award', ", "media home en")
    s = must(s, "axiomKicker: 'Distinction', ", media_keys("fr") + "axiomKicker: 'Distinction', ", "media home fr")
    s = must(s, "      praiseTop: t.praise.slice(0, 2),", "      mediaTop: t.media.slice(0, 4), praiseTop: t.praise.slice(0, 2),", "media home return")
    s = must(s, '<section class="mdd-pad" data-screen-label="About"', media_band("mediaTop", True) + '<section class="mdd-pad" data-screen-label="About"', "media home about")
    wr(p, s)
p = "speaking.html"; s = rd(p)
if MM not in s:
    s = must(s, "        kicker: 'Speaking',", "        " + media_keys("en") + "kicker: 'Speaking',", "media speaking en")
    s = must(s, "        kicker: 'Conférences',", "        " + media_keys("fr") + "kicker: 'Conférences',", "media speaking fr")
    s = must(s, "      more: t.more,", "      more: t.more, media: t.media,", "media speaking return")
    s = must(s, '<section class="mdd-pad" data-screen-label="Contact CTA"', media_band("media", False) + '<section class="mdd-pad" data-screen-label="Contact CTA"', "media speaking contact")
    wr(p, s)

# ---------- home praise: keep the two columns balanced (4 large quotes left, the rest right) ----------
p = "index.html"; s = rd(p)
OLD = "praiseTop: t.praise.slice(0, 2), praiseBottom: t.praise.slice(2),"
NEW = "praiseTop: t.praise.slice(0, 4), praiseBottom: t.praise.slice(4),"
if OLD in s:
    wr(p, s.replace(OLD, NEW, 1))
elif NEW not in s:
    sys.exit("enrich-content: ANCHOR NOT FOUND (home praise split)")

print("enrich-content: index.html, book.html, about.html enriched (Axiom band, 5 endorsements, Legion of Honour wording)")
