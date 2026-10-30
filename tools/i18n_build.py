#!/usr/bin/env python3
"""Jazykové verzie podstránok (EN / DE) zo slovenského originálu.

Slovenská stránka je zdroj pravdy. Texty sa prekladajú cez slovníky v i18n/:
  i18n/_common.<jazyk>.json   spoločné texty (menu, pätička, cookie lišta, formulár) pre všetky stránky
  i18n/<stránka>.<jazyk>.json texty konkrétnej stránky + "remove" (čo z originálu vypustiť) a "replace" (JS a iné výnimky)

Príkazy (z koreňa repozitára):
  python3 tools/i18n_build.py extract weby en   # doplní do slovníka chýbajúce texty (hodnota "")
  python3 tools/i18n_build.py build             # zostaví všetky EN/DE stránky + prepínač a hreflang v SK + sitemap.xml
  python3 tools/i18n_build.py build weby        # len jednu stránku
Build zlyhá, ak niektorý text nemá preklad — preto zmena v SK texte nikdy neostane potichu nepreložená.
Ručne sa udržiavajú: domovská stránka (index.html, en/index.html, de/index.html) a de/impressum.html.
Po každej zmene spusti aj kontrolu: python3 tools/i18n_check.py a agenta prekladovy-korektor.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "i18n"
SITE = "https://axiona-group.sk"
LANGS = ("en", "de")
LOCALE = {"sk": "sk_SK", "en": "en_GB", "de": "de_DE"}
SWITCH_LABEL = {"sk": "Jazyk", "en": "Language", "de": "Sprache"}

# URL podľa jazyka; None = stránka v jazyku neexistuje (prepínač vedie na domovskú stránku jazyka)
PAGES = {
    "home":          {"sk": "/", "en": "/en/", "de": "/de/", "manual": True},
    "ai-chatboty":   {"sk": "/ai-chatboty/", "en": "/en/ai-chatbots/", "de": "/de/ki-chatbots/"},
    "weby":          {"sk": "/weby/", "en": "/en/websites/", "de": "/de/webseiten/"},
    "automatizacie": {"sk": "/automatizacie/", "en": "/en/automation/", "de": "/de/automatisierung/"},
    "data-reporty":  {"sk": "/data-reporty/", "en": "/en/data-reporting/", "de": "/de/daten-reporting/"},
    "audity":        {"sk": "/audity/", "en": "/en/website-audit/", "de": "/de/website-audit/"},
    "privacy":       {"sk": "/privacy.html", "en": "/en/privacy.html", "de": "/de/datenschutz.html"},
    "terms":         {"sk": "/terms.html", "en": "/en/terms.html", "de": "/de/agb.html"},
    "cookies":       {"sk": "/cookies.html", "en": "/en/cookies.html", "de": "/de/cookies.html"},
}

INLINE = {"a", "b", "strong", "em", "i", "span", "br", "small", "sup", "sub", "code", "u", "mark", "abbr", "s", "wbr", "time"}
TOKEN = re.compile(r"<!--.*?-->|<script\b.*?</script>|<style\b.*?</style>|<svg\b.*?</svg>|<[^>]+>|[^<]+", re.S | re.I)
ATTRS = ("alt", "title", "placeholder", "aria-label")
META = re.compile(r'<meta\s+(?:name|property)="(description|keywords|twitter:title|twitter:description|twitter:image:alt|og:title|og:description|og:image:alt)"\s+content="([^"]*)"')
LD_KEYS = {"name", "description", "text", "serviceType", "alternateName"}
# text, ktorý sa neprekladá (značka, kontakty, čísla)
BRANDISH = re.compile(r"^(?:Axiona|GROUP|Group|Axiona Group(?: s\. r\. o\.)?|s\. r\. o\.|office@axiona-group\.sk|\+?[\d\s/()+-]+|[\W\d_]+|AI|SEO|CRM|☰|×|→)$")


def file_of(url: str) -> Path:
    p = ROOT / url.lstrip("/")
    return p / "index.html" if url.endswith("/") else p


def tag_name(tok: str) -> str:
    m = re.match(r"</?\s*([a-zA-Z0-9]+)", tok)
    return m.group(1).lower() if m else ""


def text_of(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html).strip()


BRAND_WORDS = {"Axiona", "GROUP", "Group", "s.", "r.", "o.", "AI", "SEO", "CRM", "GDPR", "Claude", "Make.com"}


def needs_translation(s: str) -> bool:
    t = re.sub(r"<[^>]+>", " ", s).replace("&amp;", "&").replace("&nbsp;", " ").strip()
    if not t or BRANDISH.match(t):
        return False
    words = [w for w in re.split(r"[\s,·|—–-]+", t) if re.search(r"[^\W\d_]", w)]
    return any(w not in BRAND_WORDS and not re.fullmatch(r"[\w.+-]+@[\w.-]+", w) for w in words)


# ---------- vyťahovanie a nahrádzanie textov ----------
def segments(html: str) -> list[str]:
    """Všetky preložiteľné texty stránky v poradí výskytu (bez duplikátov)."""
    out: list[str] = []

    def add(s: str) -> None:
        if needs_translation(s) and s not in out:
            out.append(s)

    _walk(html, lambda s: (add(s), s)[1], lambda s: (add(s), s)[1])
    return out


def _walk(html: str, on_text, on_attr) -> str:
    """Prejde HTML; on_text dostane súvislý beh textu s inline značkami, on_attr hodnotu atribútu/JS reťazca."""
    toks = TOKEN.findall(html)
    res: list[str] = []
    run: list[str] = []

    def flush() -> None:
        if not run:
            return
        raw = "".join(run)
        toks_in_run = list(run)
        run.clear()
        if not needs_translation(raw):  # bez textu na preklad: preložiť len atribúty inline značiek
            res.append("".join(_attrs(x, on_attr) if x.startswith("<") else x for x in toks_in_run))
            return
        if text_of(raw):
            lead = raw[: len(raw) - len(raw.lstrip())]
            trail = raw[len(raw.rstrip()):]
            core = raw.strip()
            res.append(lead + on_text(core) + trail)
        else:
            res.append(raw)

    for t in toks:
        low = t[:12].lower()
        if t.startswith("<"):
            if low.startswith("<script") and "ld+json" in t[:60]:
                flush()
                res.append(_ld(t, on_attr))
                continue
            if low.startswith(("<!--", "<script", "<style", "<svg")):
                flush()
                res.append(t)
                continue
            if tag_name(t) in INLINE:  # atribúty inline značiek v texte sú súčasťou prekladu celého behu
                run.append(t)
                continue
            flush()
            res.append(_attrs(t, on_attr))
        else:
            run.append(t)
    flush()
    return "".join(res)


def _attrs(tag: str, on_attr) -> str:
    def rep_attr(m):
        val = m.group(2)
        return f'{m.group(1)}="{on_attr(val) if needs_translation(val) else val}"'
    tag = re.sub(r'\b(alt|title|placeholder|aria-label)="([^"]*)"', rep_attr, tag)
    mm = META.match(tag)
    if mm and needs_translation(mm.group(2)):
        tag = tag.replace(f'content="{mm.group(2)}"', f'content="{on_attr(mm.group(2))}"')

    def rep_js(m):
        code = m.group(2)
        code = re.sub(r"'([^'\\]{4,})'", lambda s: "'" + (on_attr(s.group(1)) if (" " in s.group(1) or re.search(r"[^\x00-\x7f]", s.group(1))) and needs_translation(s.group(1)) else s.group(1)) + "'", code)
        return f'{m.group(1)}="{code}"'
    return re.sub(r'\b(on\w+)="([^"]*)"', rep_js, tag)


def _ld(tok: str, on_attr) -> str:
    head, body = tok.split(">", 1)
    body = body[: -len("</script>")]
    data = json.loads(body)

    def walk(o, key=None):
        if isinstance(o, dict):
            return {k: walk(v, k) for k, v in o.items()}
        if isinstance(o, list):
            return [walk(v, key) for v in o]
        if isinstance(o, str) and key in LD_KEYS and needs_translation(o):
            return on_attr(o)
        return o
    new = walk(data)
    return head + ">\n" + json.dumps(new, ensure_ascii=False, indent=2) + "\n</script>"


# ---------- slovníky ----------
def dict_path(key: str, lang: str) -> Path:
    return I18N / f"{key}.{lang}.json"


def load(key: str, lang: str) -> dict:
    p = dict_path(key, lang)
    d = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    d.setdefault("segments", {})
    d.setdefault("remove", [])
    d.setdefault("replace", [])
    return d


def save(key: str, lang: str, d: dict) -> None:
    I18N.mkdir(exist_ok=True)
    dict_path(key, lang).write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


# ---------- spoločné úpravy ----------
GLOBAL_REMOVE = [
    re.compile(r'\n\s*<a href="/reality/"[^>]*>[^<]*</a>'),
    re.compile(r',\s*\{\s*"@type": "Offer",\s*"itemOffered": \{\s*"@type": "Service",\s*"name": "[^"]*",\s*"url": "https://axiona-group\.sk/reality/"\s*\}\s*\}'),
]


def prepare(sk_html: str, d: dict) -> str:
    html = re.sub(r'<div class="lang-switch"[^>]*>.*?</div>', "", sk_html)  # prepínač pridá build pre každý jazyk
    html = re.sub(r'\n?<link rel="alternate" hreflang="[^"]+" href="[^"]+">', "", html)
    for rx in GLOBAL_REMOVE:
        html = rx.sub("", html)
    for r in d["remove"]:
        if r not in html:
            sys.exit(f"remove: v originále nenájdené: {r[:80]!r}")
        html = html.replace(r, "")
    return html


def alternates(key: str) -> str:
    pg = PAGES[key]
    lines = [f'<link rel="alternate" hreflang="{l}" href="{SITE}{pg[l]}">' for l in ("sk", "en", "de") if pg.get(l)]
    if pg.get("en"):
        lines.append(f'<link rel="alternate" hreflang="x-default" href="{SITE}{pg["en"]}">')
    return "\n".join(lines) + "\n"


def switcher(key: str, lang: str) -> str:
    pg = PAGES[key]
    links = []
    for l in ("sk", "en", "de"):
        url = pg.get(l) or PAGES["home"][l]
        cur = ' aria-current="page"' if l == lang else ""
        links.append(f'<a href="{url}" hreflang="{l}" lang="{l}"{cur}>{l.upper()}</a>')
    return f'<div class="lang-switch" aria-label="{SWITCH_LABEL[lang]}">' + "".join(links) + "</div>"


def versions(html: str) -> str:
    html = re.sub(r"/theme\.css\?v=\w+", "/theme.css?v=6", html)
    html = re.sub(r"/theme\.js\?v=\w+", "/theme.js?v=2", html)
    html = re.sub(r"/site\.css\?v=\w+", "/site.css?v=20261030", html)
    return re.sub(r"/site\.js\?v=\w+", "/site.js?v=20261028", html)


def add_lang_chrome(html: str, key: str, lang: str) -> str:
    html = re.sub(r'\n?<link rel="alternate" hreflang="[^"]+" href="[^"]+">', "", html)
    html = re.sub(r'<div class="lang-switch"[^>]*>.*?</div>', "", html)
    url = SITE + PAGES[key][lang]
    if '<link rel="canonical"' not in html:  # právne stránky nemali canonical ani og:locale
        html = html.replace("</head>", f'<link rel="canonical" href="{url}">\n</head>', 1)
    if '<meta property="og:locale"' not in html:
        html = html.replace('<link rel="canonical"', f'<meta property="og:locale" content="{LOCALE[lang]}">\n<link rel="canonical"', 1)
    html = html.replace('<link rel="canonical"', alternates(key) + '<link rel="canonical"', 1)
    if '<button class="theme-toggle"' not in html:
        sys.exit(f"{key}/{lang}: chýba tlačidlo motívu, kam vložiť prepínač")
    html = html.replace('<button class="theme-toggle"', switcher(key, lang) + '<button class="theme-toggle"', 1)
    return versions(html)


def relink(html: str, lang: str) -> str:
    pairs = sorted(((p["sk"], p[lang]) for p in PAGES.values() if p.get(lang) and p["sk"] != "/"), key=lambda x: -len(x[0]))
    for sk, tr in pairs:
        html = re.sub(rf'(href=["\']){re.escape(sk)}', rf"\g<1>{tr}", html)
        html = html.replace(f'"{SITE}{sk}"', f'"{SITE}{tr}"').replace(f"location.href='{sk}'", f"location.href='{tr}'")
    html = re.sub(r'href="/#', f'href="/{lang}/#', html)
    html = re.sub(r'href="(?:/|index\.html)"', f'href="/{lang}/"', html)  # logo a „späť na web“
    return html


def localize_head(html: str, key: str, lang: str) -> str:
    url = SITE + PAGES[key][lang]
    html = re.sub(r'<html lang="[^"]*"', f'<html lang="{lang}"', html, count=1)
    html = re.sub(r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="{url}">', html)
    html = re.sub(r'<meta property="og:url" content="[^"]*">', f'<meta property="og:url" content="{url}">', html)
    others = [LOCALE[l] for l in ("sk", "en", "de") if l != lang]
    html = re.sub(r'<meta property="og:locale" content="[^"]*">',
                  f'<meta property="og:locale" content="{LOCALE[lang]}">' + "".join(
                      f'\n<meta property="og:locale:alternate" content="{o}">' for o in others), html)
    return re.sub(r'"inLanguage": "[^"]*"', f'"inLanguage": "{lang}"', html)


# ---------- sitemap.xml ----------
SITEMAP_PAGES = ["home", "ai-chatboty", "weby", "automatizacie", "data-reporty", "audity"]
SITEMAP_SK_ONLY = ["/reality/"]  # stránky len po slovensky


def sitemap() -> None:
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for key in SITEMAP_PAGES:
        pg = PAGES[key]
        langs = [l for l in ("sk", "en", "de") if pg.get(l)]
        alts = [f'    <xhtml:link rel="alternate" hreflang="{l}" href="{SITE}{pg[l]}"/>' for l in langs]
        alts.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{SITE}{pg["en"]}"/>')
        for l in langs:
            out += ["  <url>", f"    <loc>{SITE}{pg[l]}</loc>", *alts, "  </url>"]
    for url in SITEMAP_SK_ONLY:
        out += ["  <url>", f"    <loc>{SITE}{url}</loc>", "  </url>"]
    out.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(out) + "\n", encoding="utf-8")


# ---------- príkazy ----------
def extract(key: str, lang: str) -> None:
    sk = file_of(PAGES[key]["sk"]).read_text(encoding="utf-8")
    d, common = load(key, lang), load("_common", lang)
    html = prepare(sk, d)
    new = [s for s in segments(html) if s not in d["segments"] and s not in common["segments"]]
    for s in new:
        d["segments"][s] = ""
    save(key, lang, d)
    print(f"{key}.{lang}: {len(new)} nových textov na preklad → {dict_path(key, lang).relative_to(ROOT)}")


def build_one(key: str) -> list[str]:
    pg = PAGES[key]
    sk_file = file_of(pg["sk"])
    sk = sk_file.read_text(encoding="utf-8")
    missing: list[str] = []
    for lang in LANGS:
        if not pg.get(lang):
            continue
        d, common = load(key, lang), load("_common", lang)
        table = {**common["segments"], **d["segments"]}
        html = prepare(sk, d)

        def tr(s: str) -> str:
            v = table.get(s)
            if not v:
                missing.append(f"{key}.{lang}: {s[:100]}")
                return s
            return v
        html = _walk(html, tr, tr)
        for a, b in common["replace"]:  # spoločné náhrady len tam, kde sa text vyskytuje
            html = html.replace(a, b)
        for a, b in d["replace"]:
            if a not in html:
                missing.append(f"{key}.{lang}: replace nenájdené: {a[:80]}")
            html = html.replace(a, b)
        html = localize_head(html, key, lang)
        html = relink(html, lang)
        html = add_lang_chrome(html, key, lang)
        out = file_of(pg[lang])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")
    # slovenský originál: len prepínač, hreflang a verzie súborov
    sk_file.write_text(add_lang_chrome(sk, key, "sk"), encoding="utf-8")
    return missing


def main(argv: list[str]) -> int:
    if len(argv) >= 3 and argv[0] == "extract":
        extract(argv[1], argv[2])
        return 0
    if argv and argv[0] == "build":
        keys = argv[1:] or [k for k, v in PAGES.items() if not v.get("manual")]
        missing = []
        for k in keys:
            if PAGES[k].get("manual"):
                continue
            missing += build_one(k)
            print("zostavené:", k)
        if not argv[1:]:
            sitemap()
            print("zostavené: sitemap.xml")
        for m in missing:
            print("CHÝBA PREKLAD ", m)
        return 1 if missing else 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
