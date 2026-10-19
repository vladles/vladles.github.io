"""Checks for the static site. Run: python3 -m unittest discover -s tests -v"""

import json
import re
import subprocess
import unittest
import xml.etree.ElementTree as ET
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

    def test_internal_dirs_ignored(self):
        for path in [".claude/worktrees/x/index.html", ".claude/settings.json", ".superpowers/notes.md"]:
            r = subprocess.run(["git", "check-ignore", "-q", "--no-index", path], cwd=ROOT)
            self.assertEqual(r.returncode, 0, path)

    def test_only_site_files_are_published(self):
        published = {"index.html", "assets", "CNAME", "robots.txt", "sitemap.xml"}
        cfg = (ROOT / "_config.yml").read_text()
        excluded = set(re.findall(r"(?m)^\s*-\s*(\S+)\s*$", cfg))
        tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout
        top = {line.split("/")[0] for line in tracked.splitlines()}
        leaks = {n for n in top if n not in published | excluded and not n.startswith((".", "_"))}
        self.assertEqual(leaks, set(), "add to _config.yml exclude or to the published allowlist")

    def test_font_license_shipped(self):
        text = (ROOT / "assets" / "fonts" / "OFL.txt").read_text()
        self.assertIn("SIL OPEN FONT LICENSE Version 1.1", text)
        self.assertIn("Fraunces Project Authors", text)
        self.assertIn("Open Sans Project Authors", text)

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

    def test_avatar_serves_small_file_at_display_size(self):
        img = next(i for i in Page.load().imgs if i["src"].endswith("avatar.jpg"))
        self.assertIn("/assets/avatar-192.jpg 192w", img.get("srcset", ""))
        self.assertEqual(img.get("sizes"), "96px")
        self.assertEqual(jpeg_size(ROOT / "assets" / "avatar-192.jpg"), (192, 192))


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

    def test_fonts_self_hosted_with_swap(self):
        p, c = Page.load(), css()
        self.assertNotIn("fonts.googleapis.com", p.raw)  # no render-blocking third-party CSS
        faces = re.findall(r"@font-face\s*\{(.*?)\}", c, re.S)
        self.assertEqual({re.search(r'font-family:\s*"([^"]+)"', f).group(1) for f in faces},
                         {"Fraunces", "Open Sans"})
        for f in faces:
            self.assertIn("font-display: swap", f)
            url = re.search(r"url\(\"?(/assets/fonts/[^)\"]+\.woff2)", f).group(1)
            self.assertTrue((ROOT / url.lstrip("/")).exists(), url)

    def test_fonts_preloaded(self):
        preloads = [l for l in Page.load().links if l.get("rel") == "preload"]
        hrefs = {l["href"] for l in preloads if l.get("as") == "font" and "crossorigin" in l}
        self.assertTrue(any("fraunces" in h for h in hrefs) and any("open-sans" in h for h in hrefs), hrefs)

    def test_favicon(self):
        links = Page.load().links
        self.assertTrue(any(l.get("rel") == "icon" and l.get("href") == "/assets/favicon.svg" for l in links))
        self.assertTrue((ROOT / "assets" / "favicon.svg").exists())


def jpeg_size(path: Path) -> tuple[int, int]:
    """(width, height) of a JPEG, read from its SOF marker."""
    data = path.read_bytes()
    i = 2
    while i < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            h = int.from_bytes(data[i + 5:i + 7], "big")
            w = int.from_bytes(data[i + 7:i + 9], "big")
            return w, h
        i += 2 + int.from_bytes(data[i + 2:i + 4], "big")
    raise ValueError(f"no SOF marker in {path}")


DESC = ("Vlad Lesovskiy — Lead Software Engineer in Belgrade. 10+ years building web and mobile "
        "products with Laravel, Next.js and AWS. Open to new opportunities.")


class SeoTests(unittest.TestCase):
    def test_title_and_description(self):
        p = Page.load()
        self.assertEqual(p.title, "Vlad Lesovskiy — Lead Software Engineer")
        for k in ["description", "og:description", "twitter:description"]:
            self.assertEqual(p.meta(k), DESC)
        self.assertLessEqual(len(DESC), 160)

    def test_canonical_and_lang(self):
        p = Page.load()
        canon = [l.get("href") for l in p.links if l.get("rel") == "canonical"]
        self.assertEqual(canon, ["https://lesovskiy.com/"])
        self.assertIn('<html lang="en"', p.raw)

    def test_open_graph(self):
        p = Page.load()
        expected = {"og:type": "profile", "og:url": "https://lesovskiy.com/",
                    "og:title": "Vlad Lesovskiy — Lead Software Engineer",
                    "og:image:width": "1200", "og:image:height": "630",
                    "profile:first_name": "Vlad", "profile:last_name": "Lesovskiy",
                    "twitter:card": "summary_large_image"}
        for k, v in expected.items():
            self.assertEqual(p.meta(k), v, k)

    def test_og_image_absolute_and_exists(self):
        p = Page.load()
        self.assertEqual(p.meta("og:image"), "https://lesovskiy.com/assets/og.jpg")
        self.assertEqual(jpeg_size(ROOT / "assets" / "og.jpg"), (1200, 630))

    def test_jsonld_person(self):
        d = Page.load().jsonld[0]
        self.assertEqual((d["@type"], d["name"], d["alternateName"]),
                         ("Person", "Vlad Lesovskiy", "Влад Лесовский"))
        self.assertEqual(d["url"], "https://lesovskiy.com/")
        self.assertIn("https://www.linkedin.com/in/vladles95", d["sameAs"])
        self.assertEqual(d["address"]["addressCountry"], "RS")

    def test_robots_and_sitemap(self):
        self.assertIn("Sitemap: https://lesovskiy.com/sitemap.xml", (ROOT / "robots.txt").read_text())
        ET.parse(ROOT / "sitemap.xml")
        self.assertIn("<loc>https://lesovskiy.com/</loc>", (ROOT / "sitemap.xml").read_text())


if __name__ == "__main__":
    unittest.main()
