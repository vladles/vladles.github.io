"""Checks for the static site. Run: python3 -m unittest discover -s tests -v"""

import json
import re
import subprocess
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class Page(HTMLParser):
    """Parsed view of an HTML page: text, meta tags, links, images, ids, JSON-LD."""

    SKIP_TEXT = {"script", "style", "head"}

    def __init__(self, raw: str):
        super().__init__(convert_charrefs=True)
        self.raw = raw
        self.title = ""
        self.links: list[dict] = []
        self.anchors: list[str] = []
        self.imgs: list[dict] = []
        self.ids: set[str] = set()
        self.jsonld: list[dict] = []
        self._metas: list[dict] = []
        self._counts: dict[str, int] = {}
        self._text: list[str] = []
        self._stack: list[str] = []
        self._in_jsonld = False
        self._buf: list[str] = []
        self.feed(raw)
        self.close()
        self.text = re.sub(r"\s+", " ", " ".join(self._text)).strip()

    @classmethod
    def load(cls, path: Path = ROOT / "index.html") -> "Page":
        return cls(path.read_text(encoding="utf-8"))

    def meta(self, key: str) -> str | None:
        for m in self._metas:
            if m.get("name") == key or m.get("property") == key:
                return m.get("content")
        return None

    def count(self, tag: str) -> int:
        return self._counts.get(tag, 0)

    def handle_starttag(self, tag, attrs):
        a = {k: (v or "") for k, v in attrs}
        self._counts[tag] = self._counts.get(tag, 0) + 1
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "meta":
            self._metas.append(a)
        elif tag == "link":
            self.links.append(a)
        elif tag == "a" and "href" in a:
            self.anchors.append(a["href"])
        elif tag == "img":
            self.imgs.append(a)
        elif tag == "script" and a.get("type") == "application/ld+json":
            self._in_jsonld = True
            self._buf = []
        if tag not in {"meta", "link", "img", "br", "hr", "input"}:
            self._stack.append(tag)

    def handle_endtag(self, tag):
        if tag == "script" and self._in_jsonld:
            self.jsonld.append(json.loads("".join(self._buf)))
            self._in_jsonld = False
        if tag in self._stack:
            while self._stack and self._stack.pop() != tag:
                pass

    def handle_data(self, data):
        if self._in_jsonld:
            self._buf.append(data)
        if self._stack and self._stack[-1] == "title":
            self.title += data.strip()
        if not self.SKIP_TEXT & set(self._stack):
            self._text.append(data)


class PublishingTests(unittest.TestCase):
    def test_jekyll_excludes_internal_files(self):
        cfg = (ROOT / "_config.yml").read_text()
        for item in ["docs", "tests", "tools", "CLAUDE.md", "README.md"]:
            self.assertRegex(cfg, rf"(?m)^\s*-\s*{re.escape(item)}\s*$")

    def test_cv_pdf_is_ignored(self):
        r = subprocess.run(["git", "check-ignore", "-q", "Vlad_Lesovskiy_CV.pdf"], cwd=ROOT)
        self.assertEqual(r.returncode, 0)

    def test_page_parses(self):
        self.assertEqual(Page.load().count("html"), 1)


class ContentTests(unittest.TestCase):
    def test_single_h1_is_name(self):
        p = Page.load()
        self.assertEqual(p.count("h1"), 1)
        self.assertIn("Vlad Lesovskiy", p.text)

    def test_sections_present(self):
        expected = {"intro", "experience", "skills", "education", "outside", "contact"}
        self.assertTrue(expected <= Page.load().ids)

    def test_contact_links(self):
        a = Page.load().anchors
        for href in ["https://t.me/vladles", "mailto:inbox@lesovskiy.com",
                     "https://www.linkedin.com/in/vladles95", "https://github.com/vladles"]:
            self.assertIn(href, a)

    def test_telegram_cta_and_availability(self):
        t = Page.load().text
        self.assertIn("Message me on Telegram", t)
        self.assertEqual(t.count("Open to new opportunities"), 1)

    def test_experience_entries(self):
        t = Page.load().text
        for s in ["MaxRx", "Jun 2025 – Present", "CharityRx", "Jan 2020 – Jan 2026",
                  "Pix Wireless", "Jan 2018 – Aug 2023", "CimpleO", "WordPress Monsters"]:
            self.assertIn(s, t)

    def test_forbidden_content(self):
        r = Page.load().raw
        for s in ["lesovskiy.ru", "bulma", "Vlad_Lesovskiy_CV.pdf", "I started as WordPress", "<script src"]:
            self.assertNotIn(s, r)

    def test_yandex_verification_kept(self):
        self.assertEqual(Page.load().meta("yandex-verification"), "691bad7d13005913")

    def test_avatar_has_alt_and_size(self):
        img = next(i for i in Page.load().imgs if i["src"].endswith("avatar.jpg"))
        self.assertEqual((img.get("alt"), img.get("width"), img.get("height")),
                         ("Vlad Lesovskiy", "640", "640"))


def css() -> str:
    return (ROOT / "assets" / "styles.css").read_text()


def dark_block(text: str) -> str:
    m = re.search(r"@media\s*\(prefers-color-scheme:\s*dark\)\s*\{(.*?)\n\}", text, re.S)
    return m.group(1) if m else ""


class StyleTests(unittest.TestCase):
    def test_css_has_dark_mode(self):
        block = dark_block(css())
        for var in ["--bg", "--text", "--accent"]:
            self.assertIn(var, block)

    def test_css_prevents_overflow(self):
        c = css()
        self.assertIn("overflow-wrap: anywhere", c)
        self.assertRegex(c, r"img\s*\{[^}]*max-width:\s*100%")

    def test_font_fallbacks(self):
        c = css()
        self.assertRegex(c, r'"Fraunces",[^;]*\bserif;')
        self.assertRegex(c, r'"Open Sans",[^;]*\bsans-serif;')

    def test_fonts_swap_and_preconnect(self):
        links = Page.load().links
        self.assertTrue(any(l.get("rel") == "stylesheet" and "display=swap" in l.get("href", "") for l in links))
        self.assertTrue(any(l.get("rel") == "preconnect" and l.get("href") == "https://fonts.gstatic.com" for l in links))

    def test_favicon(self):
        links = Page.load().links
        self.assertTrue(any(l.get("rel") == "icon" and l.get("href") == "/assets/favicon.svg" for l in links))
        self.assertTrue((ROOT / "assets" / "favicon.svg").exists())


class SeoTests(unittest.TestCase):
    pass


if __name__ == "__main__":
    unittest.main()
