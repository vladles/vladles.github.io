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
    pass


class StyleTests(unittest.TestCase):
    pass


class SeoTests(unittest.TestCase):
    pass


if __name__ == "__main__":
    unittest.main()
