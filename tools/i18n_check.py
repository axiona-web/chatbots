#!/usr/bin/env python3
"""Kontrola jazykových verzií webu (SK / EN / DE) — strojová časť.

Spustenie z koreňa repozitára:  python3 tools/i18n_check.py
Kontroluje: lang a og:locale, canonical, vzájomné hreflang odkazy, x-default, odkazy v EN/DE vedúce na
slovenské stránky alebo na neexistujúce súbory, slovenské zvyšky v texte a zhodu cien (€) so slovenským
originálom. Jazyk, gramatiku a vernosť prekladu kontroluje agent „prekladovy-korektor“ (.claude/agents/).
Návratový kód 1 = našli sa chyby (CHYBA); upozornenia (POZOR) kód nemenia.
"""
from __future__ import annotations

import html
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://axiona-group.sk"
LANGS = ("sk", "en", "de")
LOCALE = {"sk": "sk_SK", "en": "en_GB", "de": "de_DE"}
# slová so slovenskou diakritikou, ktoré sú v EN/DE správne (vlastné mená, adresa, IČO/DIČ)
ALLOW = {"IČO", "DIČ", "Kaštieľom", "Smižany", "Smižanoch", "Košice", "Spišská", "Nová", "Ves"}
SK_ONLY = re.compile(r"\b\w*[čťľďňôŕĺžšýáíéúČŤĽĎŇŽŠÝÁÍÉÚ]\w*\b")
# cesty, ktoré nie sú stránky (súbory, externé časti) — odkaz na ne z EN/DE je v poriadku
ASSET = re.compile(r"\.(png|jpe?g|svg|webp|gif|ico|css|js|pdf|xml|txt|woff2?|mp4)$|^/fonts/", re.I)
EXTERNAL_OK = ("https://projekty.axiona-group.sk",)


class Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lang = None
        self.canonical = None
        self.locale = None
        self.alternates: dict[str, str] = {}
        self.links: list[str] = []
        self.text: list[str] = []
        self.attr_text: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.lang = a.get("lang")
        if tag == "link" and a.get("rel") == "canonical":
            self.canonical = a.get("href")
        if tag == "link" and a.get("rel") == "alternate" and a.get("hreflang"):
            self.alternates[a["hreflang"]] = a.get("href", "")
        if tag == "meta" and a.get("property") == "og:locale":
            self.locale = a.get("content")
        if tag == "meta" and (a.get("name") in ("description", "keywords", "twitter:title", "twitter:description")
                              or (a.get("property") or "").startswith("og:") and a.get("property") not in ("og:url", "og:image", "og:locale", "og:locale:alternate")):
            self.attr_text.append(a.get("content") or "")
        for k in ("alt", "title", "placeholder", "aria-label"):
            if a.get(k):
                self.attr_text.append(a[k])
        if tag == "a" and a.get("href") and not a.get("hreflang"):  # odkazy prepínača jazyka (hreflang) sú zámerne inde
            self.links.append(a["href"])
        if tag in ("script", "style", "svg"):
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style", "svg") and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip and data.strip():
            self.text.append(data)


def parse(path: Path) -> Page:
    p = Page()
    raw = path.read_text(encoding="utf-8")
    p.feed(raw)
    p.raw = raw  # type: ignore[attr-defined]
    return p


def url_to_file(url: str) -> Path | None:
    if url.startswith(SITE):
        url = url[len(SITE):]
    if not url.startswith("/"):
        return None
    url = url.split("#")[0].split("?")[0]
    f = ROOT / url.lstrip("/")
    if url.endswith("/"):
        f = f / "index.html"
    return f


def prices(p: Page) -> list[str]:
    """Sumy v eurách, normalizované („100 €“ = „€100“ = „100,00 €“)."""
    txt = html.unescape(" ".join(p.text + p.attr_text)).replace(" ", " ")
    found = re.findall(r"€\s?(\d[\d ]*(?:[.,]\d+)?)|(\d[\d ]*(?:[.,]\d+)?)\s?€", txt)
    out = []
    for a, b in found:
        v = (a or b).replace(" ", "").replace(",", ".")
        out.append(str(float(v)).rstrip("0").rstrip("."))
    return sorted(out, key=float)


def main() -> int:
    errors, warns = [], []
    pages = {}
    for f in sorted(ROOT.rglob("*.html")):
        rel = f.relative_to(ROOT)
        if rel.parts[0] in (".git", "node_modules", "tools"):
            continue
        p = parse(f)
        if p.alternates:
            pages[f] = p

    for f, p in pages.items():
        rel = f.relative_to(ROOT)
        lang = (p.lang or "").split("-")[0]
        me = f"{rel}"
        if lang not in LANGS:
            errors.append(f"{me}: <html lang> je „{p.lang}“")
            continue
        own = p.alternates.get(lang)
        if not own:
            errors.append(f"{me}: chýba hreflang na seba ({lang})")
        if p.canonical != own:
            errors.append(f"{me}: canonical {p.canonical} ≠ hreflang {lang} {own}")
        if "x-default" not in p.alternates:
            errors.append(f"{me}: chýba hreflang x-default")
        if p.locale != LOCALE[lang]:
            errors.append(f"{me}: og:locale je {p.locale}, má byť {LOCALE[lang]}")
        for hl, url in p.alternates.items():
            tf = url_to_file(url)
            if tf is None or not tf.exists():
                errors.append(f"{me}: hreflang {hl} → {url} neexistuje")
                continue
            if hl == "x-default":
                continue
            other = pages.get(tf)
            if other is None or other.alternates.get(lang) != own:
                errors.append(f"{me}: {url} neodkazuje späť cez hreflang {lang}")

        if lang == "sk":
            continue
        # odkazy z EN/DE stránky
        for href in p.links:
            if href.startswith(("mailto:", "tel:", "#", "javascript:")) or href.startswith(EXTERNAL_OK):
                continue
            if href.startswith("http") and not href.startswith(SITE):
                continue
            path = href[len(SITE):] if href.startswith(SITE) else href
            if ASSET.search(path.split("#")[0].split("?")[0]):
                continue
            if not path.startswith(f"/{lang}/"):
                errors.append(f"{me}: odkaz vedie mimo /{lang}/ (na slovenskú stránku?): {href}")
                continue
            tf = url_to_file(path)
            if tf is not None and not tf.exists():
                w = f"{me}: odkaz na stránku, ktorá ešte neexistuje: {href.split('#')[0]}"
                if w not in warns:
                    warns.append(w)
        # slovenské zvyšky
        visible = html.unescape(" ".join(p.text + p.attr_text))
        left = sorted({w for w in SK_ONLY.findall(visible) if w not in ALLOW
                       and not (lang == "de" and not re.search(r"[čťľďňôŕĺžšýáíéúČŤĽĎŇŽŠÝÁÍÉÚ]", w.replace("é", "")))})
        if left:
            errors.append(f"{me}: slová so slovenskou diakritikou: {', '.join(left[:20])}")
        # ceny oproti slovenskému originálu
        sk_file = url_to_file(p.alternates.get("sk", ""))
        if sk_file in pages:
            a, b = prices(pages[sk_file]), prices(p)
            if a != b:
                errors.append(f"{me}: ceny nesedia so SK verziou\n      SK: {a}\n      {lang.upper()}: {b}")

    for e in errors:
        print("CHYBA ", e)
    for w in warns:
        print("POZOR ", w)
    print(f"\n{len(pages)} stránok s jazykovými verziami · {len(errors)} chýb · {len(warns)} upozornení")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
