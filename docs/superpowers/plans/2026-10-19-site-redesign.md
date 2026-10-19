# lesovskiy.com Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Bulma bio page with a single, simple, SEO-optimized English "presentation" page built from Vlad's CV, whose main action is messaging him on Telegram.

**Architecture:** One static `index.html` and one hand-written `assets/styles.css`, with no JS, no framework and no build step, served by GitHub Pages (Jekyll) at `lesovskiy.com`. A Python stdlib test suite (`tests/test_site.py`) parses the HTML and asserts content, links and SEO tags. A `_config.yml` keeps internal files (docs, tests, tools, CLAUDE.md) from being published. The share image is rendered once from an HTML template with headless Chrome and committed.

**Tech Stack:** HTML5, CSS (custom properties, `prefers-color-scheme`), Google Fonts (Fraunces + Open Sans), JSON-LD schema.org `Person`, Python 3 `unittest` + `html.parser`, headless Google Chrome + `sips` for the share image.

**Spec:** `docs/superpowers/specs/2026-10-19-site-redesign-design.md`

## Global Constraints

- English only. No Russian version.
- Name forms: exactly "Vlad Lesovskiy" and, in structured data only, "Влад Лесовский". Never invent a formal first name.
- Main action: Telegram `https://t.me/vladles`. Then email `inbox@lesovskiy.com`, LinkedIn `https://www.linkedin.com/in/vladles95`, GitHub `https://github.com/vladles`.
- "Open to new opportunities" appears once in the intro and in the meta/OG description. No terms (remote, contract, …).
- The CV PDF (`Vlad_Lesovskiy_CV.pdf`) is never committed or linked.
- Keep `<meta name="yandex-verification" content="691bad7d13005913" />`.
- No `lesovskiy.ru` link anywhere. No Bulma.
- Canonical URL: `https://lesovskiy.com/`.
- Fonts: Fraunces (name + headings), Open Sans (body), Google Fonts with `display=swap`.
- Layout: single column, max width `680px`, light by default with automatic dark mode.
- No JavaScript on the page.

## Review Focus

1. **Phone width 320px:** no horizontal scroll; long words (emails, URLs) wrap; the avatar and name stack cleanly. Pinned by `test_css_prevents_overflow` (Task 2) and a manual check at 320px (Task 5).
2. **Dark mode:** body text, links and the Telegram button stay readable (contrast ≥ 4.5:1). Pinned by `test_css_has_dark_mode` (Task 2) and a manual check (Task 5).
3. **Google Fonts blocked or slow:** text shows immediately in fallback fonts. Pinned by `test_font_fallbacks` (Task 2).
4. **Share previews:** Telegram and LinkedIn need an absolute `https://` `og:image` that really exists at 1200×630. Pinned by `test_og_image_absolute_and_exists` (Task 3).
5. **Internal files leaking:** Jekyll would publish `docs/`, `tests/`, `tools/`, `CLAUDE.md` and `README.md` as public pages. Pinned by `test_jekyll_excludes_internal_files` (Task 1).

---

### Task 1: Publishing guardrails and test harness

**Files:**
- Create: `_config.yml`
- Modify: `.gitignore`
- Create: `tests/test_site.py`
- Commit: `docs/superpowers/specs/2026-10-19-site-redesign-design.md`, this plan

**Interfaces:**
- Produces, in `tests/test_site.py`:
  - `ROOT: pathlib.Path`, the repo root (`Path(__file__).resolve().parent.parent`)
  - `class Page`, built by `Page.load(path: Path = ROOT / "index.html")`, with:
    - `text: str` (visible text, whitespace collapsed, excluding `<script>`/`<style>`/`<head>`)
    - `meta(key: str) -> str | None` (matches the `name` or `property` attribute and returns `content`)
    - `links: list[dict]` (attrs of every `<link>`)
    - `anchors: list[str]` (every `<a href>`)
    - `imgs: list[dict]` (attrs of every `<img>`)
    - `count(tag: str) -> int`
    - `ids: set[str]`
    - `title: str`
    - `jsonld: list[dict]` (parsed `<script type="application/ld+json">` blocks)
    - `raw: str`
  - Test classes `PublishingTests`, `ContentTests`, `StyleTests`, `SeoTests`. Later tasks add methods to these.

- [ ] **Step 1: Write the failing tests** in `PublishingTests`:

```python
def test_jekyll_excludes_internal_files(self):
    cfg = (ROOT / "_config.yml").read_text()
    for item in ["docs", "tests", "tools", "CLAUDE.md", "README.md"]:
        self.assertRegex(cfg, rf"(?m)^\s*-\s*{re.escape(item)}\s*$")

def test_cv_pdf_is_ignored(self):
    r = subprocess.run(["git", "check-ignore", "-q", "Vlad_Lesovskiy_CV.pdf"], cwd=ROOT)
    self.assertEqual(r.returncode, 0)

def test_page_parses(self):
    self.assertEqual(Page.load().count("html"), 1)
```

- [ ] **Step 2: Run the tests and confirm the first two fail.**
Run: `python3 -m unittest discover -s tests -v`
Expected: `test_jekyll_excludes_internal_files` FAILS (no `_config.yml`), `test_cv_pdf_is_ignored` FAILS, `test_page_parses` passes.

- [ ] **Step 3: Implement.** `_config.yml` contains an `exclude:` YAML list with exactly those five entries. Append `Vlad_Lesovskiy_CV.pdf` to `.gitignore`, keeping `.DS_Store`. Implement `Page` with `html.parser.HTMLParser`.

- [ ] **Step 4: Run the tests and confirm all three pass.**
Run: `python3 -m unittest discover -s tests -v`
Expected: 3 tests, OK.

- [ ] **Step 5: Commit**

```bash
git add _config.yml .gitignore tests/test_site.py docs/superpowers
git commit -m "chore: exclude internal files from Pages, ignore CV, add site tests"
```

---

### Task 2: New page content, structure and styles

**Files:**
- Rewrite: `index.html` (body and the non-SEO parts of `<head>`)
- Rewrite: `assets/styles.css`
- Create: `assets/favicon.svg`
- Modify: `tests/test_site.py` (`ContentTests`, `StyleTests`)

**Interfaces:**
- Consumes: `Page`, `ROOT` (Task 1).
- Produces: section ids `intro`, `experience`, `skills`, `education`, `outside`, `contact`. Task 3 adds tags to `<head>` only.

**Exact copy.** Use this text verbatim; markup is the implementer's choice.

- **Intro:**
  - `h1` "Vlad Lesovskiy"
  - Subtitle "Lead Software Engineer · Belgrade, Serbia"
  - Paragraph: "I build web and mobile products end to end — from business requirements and architecture to production launch. 10+ years with PHP/Laravel, TypeScript, React/Next.js and AWS, most recently on healthcare and telehealth platforms."
  - Status line: "Open to new opportunities."
  - Primary button: "Message me on Telegram" → Telegram
  - Secondary link: "inbox@lesovskiy.com" → `mailto:`
  - Round avatar `assets/avatar.jpg`, `alt="Vlad Lesovskiy"`, `width="640" height="640"`
- **Experience** (heading "Experience"). Each entry has a role line, dates, a one-line product description and bullets:
  - **MaxRx** — Lead Developer — Jun 2025 – Present — "Healthcare e-commerce and telehealth platform for men's health."
    - "Architected the platform and delivered the MVP in 5 months — from product selection and intake to prescription and medication delivery."
    - "Integrated 2 medical providers (REST and GraphQL) behind a shared form model, provider adapters and a state machine."
    - "Owned AWS infrastructure, infrastructure as code and CI/CD; built Chargebee billing and a Filament admin platform."
  - **CharityRx** — Lead Developer — Jan 2020 – Jan 2026 — "Prescription savings platform that also supports charities."
    - "Owned the architecture and built the full backend, from inception to production."
    - "Built search across tens of thousands of FDA/DrugBank medication records with GLIC and Optum pricing."
    - "Migrated the website to Next.js for SEO and shipped React Native apps to the App Store and Google Play."
  - **Pix Wireless** — Full-Stack Developer / Team Lead — Jan 2018 – Aug 2023 — "B2C mobile services platform integrating 3 operators."
    - "Owned the architecture and MVNO integrations: registration, number assignment, purchase and activation."
    - "Led delivery in a 10-person engineering and design team: planning, milestones and hiring."
  - **Earlier** (no bullets): "CimpleO — Web Developer, 2017–2019" and "WordPress Monsters — WordPress Developer, 2016–2017"
- **Skills** (heading "Skills"): label + line rows, copied from the CV:
  - Backend & data — PHP, Laravel, REST APIs, queues, event-driven workflows, MySQL, PostgreSQL, Redis
  - Frontend & mobile — TypeScript, Next.js, React, React Native, Angular, Vue
  - Cloud & delivery — AWS ECS/Fargate, RDS, S3, SQS, CloudFront; Docker; CI/CD; infrastructure as code
  - Integrations — Third-party APIs, subscriptions and billing, telecom services, healthcare platforms
  - Architecture & leadership — System architecture, technical ownership, requirements, team coordination
  - AI-assisted engineering — Claude Code, custom agents and skills, RAG, function calling
- **Education** (heading "Education & languages"): "BSc in Applied Mathematics and Physics, Omsk State University · Russian (native), English (B2)"
- **Outside work** (heading "Outside work"): "I volunteer as an event organizer in the vas3k community, running events for 100+ people. A few years ago I got into sailing — now I organize charters with friends and help newcomers get started." Link "vas3k" → `https://vas3k.club/`.
- **Contact card footer** (`id="contact"`): "Vlad Lesovskiy" / "Lead Software Engineer" / "Belgrade, Serbia", then links Telegram, inbox@lesovskiy.com, LinkedIn, GitHub. External links get `rel="noopener"`, with no `target="_blank"` on mailto.

**Style values** (`assets/styles.css`, custom properties on `:root`):
- Light: `--bg #fbfaf7`, `--text #1c1b19`, `--muted #6b6760`, `--accent #1f4fd1`, `--rule #e7e3dc`
- Dark (`@media (prefers-color-scheme: dark)`): `--bg #141413`, `--text #ecebe7`, `--muted #a29e96`, `--accent #8fb0ff`, `--rule #2c2b29`
- Body is Open Sans 17px / 1.65. `h1` and `h2` are Fraunces. The column is `max-width: 680px` with `padding-inline: 20px`.
- Telegram button: solid `--accent` background with `--bg` text.
- Avatar: 96px circle beside the name on wide screens, stacked above it below 480px.
- Favicon: `assets/favicon.svg`, a circle in `#1f4fd1` with a white "VL" monogram.
- `<head>` loads fonts with `<link rel="preconnect">` to `fonts.googleapis.com` and `fonts.gstatic.com` (crossorigin), then the stylesheet `https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Open+Sans:wght@400;600&display=swap`.

- [ ] **Step 1: Write the failing tests.**

`ContentTests`:

```python
def test_single_h1_is_name(self):
    p = Page.load(); self.assertEqual(p.count("h1"), 1); self.assertIn("Vlad Lesovskiy", p.text)

def test_sections_present(self):
    self.assertTrue({"intro","experience","skills","education","outside","contact"} <= Page.load().ids)

def test_contact_links(self):
    a = Page.load().anchors
    for href in ["https://t.me/vladles", "mailto:inbox@lesovskiy.com",
                 "https://www.linkedin.com/in/vladles95", "https://github.com/vladles"]:
        self.assertIn(href, a)

def test_telegram_cta_and_availability(self):
    t = Page.load().text
    self.assertIn("Message me on Telegram", t); self.assertEqual(t.count("Open to new opportunities"), 1)

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
    self.assertEqual((img.get("alt"), img.get("width"), img.get("height")), ("Vlad Lesovskiy", "640", "640"))
```

`StyleTests` (read `assets/styles.css` as text):

```python
def test_css_has_dark_mode(self):       # prefers-color-scheme: dark redefines --bg, --text, --accent
def test_css_prevents_overflow(self):   # contains "overflow-wrap: anywhere" and "max-width: 100%" for img
def test_font_fallbacks(self):          # Fraunces stack ends in serif; Open Sans stack ends in sans-serif
def test_fonts_swap_and_preconnect(self):  # a stylesheet link href contains "display=swap"; preconnect to fonts.gstatic.com present
def test_favicon(self):                 # <link rel="icon" href="/assets/favicon.svg"> exists and file exists
```

- [ ] **Step 2: Run the tests and confirm the new ones fail.**
Run: `python3 -m unittest discover -s tests -v`
Expected: ContentTests and StyleTests FAIL. `test_yandex_verification_kept` already passes.

- [ ] **Step 3: Rewrite `index.html`, `assets/styles.css` and create `assets/favicon.svg`** with the copy and values above.

- [ ] **Step 4: Run the tests and confirm all pass.**
Run: `python3 -m unittest discover -s tests -v`
Expected: OK.

- [ ] **Step 5: Look at it.** Run `python3 -m http.server 8000` and open http://localhost:8000. Check the page at 1280px and 320px, and in both light and dark mode (DevTools → Rendering → `prefers-color-scheme`). There should be no horizontal scroll at 320px.

- [ ] **Step 6: Commit**

```bash
git add index.html assets/styles.css assets/favicon.svg tests/test_site.py
git commit -m "feat: new single-page presentation layout and content"
```

---

### Task 3: SEO, structured data and share image

**Files:**
- Modify: `index.html` (`<head>` only)
- Create: `robots.txt`, `sitemap.xml`
- Create: `tools/og.html`, `assets/og.jpg`
- Modify: `tests/test_site.py` (`SeoTests`)

**Interfaces:**
- Consumes: `Page`, `ROOT` (Task 1); section ids (Task 2).

**Exact values:**
- `<title>`: `Vlad Lesovskiy — Lead Software Engineer`
- Description, used for `description`, `og:description` and `twitter:description`: `Vlad Lesovskiy — Lead Software Engineer in Belgrade. 10+ years building web and mobile products with Laravel, Next.js and AWS. Open to new opportunities.`
- `<link rel="canonical" href="https://lesovskiy.com/">`
- `og:type` = `profile`, `og:url` = `https://lesovskiy.com/`, `og:title` = the title, `og:image` = `https://lesovskiy.com/assets/og.jpg`, `og:image:width` = `1200`, `og:image:height` = `630`, `profile:first_name` = `Vlad`, `profile:last_name` = `Lesovskiy`, `twitter:card` = `summary_large_image`
- JSON-LD:

```json
{
  "@context": "https://schema.org",
  "@type": "Person",
  "name": "Vlad Lesovskiy",
  "alternateName": "Влад Лесовский",
  "jobTitle": "Lead Software Engineer",
  "url": "https://lesovskiy.com/",
  "image": "https://lesovskiy.com/assets/avatar.jpg",
  "email": "mailto:inbox@lesovskiy.com",
  "address": {"@type": "PostalAddress", "addressLocality": "Belgrade", "addressCountry": "RS"},
  "alumniOf": {"@type": "CollegeOrUniversity", "name": "Omsk State University"},
  "knowsAbout": ["PHP", "Laravel", "TypeScript", "React", "Next.js", "AWS", "React Native", "Healthcare platforms"],
  "sameAs": ["https://www.linkedin.com/in/vladles95", "https://github.com/vladles", "https://t.me/vladles"]
}
```

- `robots.txt`: `User-agent: *`, `Allow: /`, `Sitemap: https://lesovskiy.com/sitemap.xml`
- `sitemap.xml`: one `<url>` with `<loc>https://lesovskiy.com/</loc>` and `<lastmod>` = the commit date.
- Share image: `tools/og.html` is a 1200×630 page using the Task 2 light palette and fonts, with the avatar (left, round, 280px), "Vlad Lesovskiy" in Fraunces and "Lead Software Engineer · Belgrade" beneath it. Render and convert it:

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu \
  --hide-scrollbars --window-size=1200,630 --screenshot=/tmp/og.png "file://$PWD/tools/og.html"
sips -s format jpeg -s formatOptions 85 /tmp/og.png --out assets/og.jpg
```

  `tools/og.html` references the avatar as `../assets/avatar.jpg`.

- [ ] **Step 1: Write the failing tests** in `SeoTests`:

```python
DESC = "Vlad Lesovskiy — Lead Software Engineer in Belgrade. 10+ years building web and mobile products with Laravel, Next.js and AWS. Open to new opportunities."

def test_title_and_description(self):
    p = Page.load(); self.assertEqual(p.title, "Vlad Lesovskiy — Lead Software Engineer")
    for k in ["description", "og:description", "twitter:description"]: self.assertEqual(p.meta(k), DESC)
    self.assertLessEqual(len(DESC), 160)

def test_canonical_and_lang(self):  # canonical href == "https://lesovskiy.com/"; '<html lang="en"' in raw

def test_og_image_absolute_and_exists(self):
    p = Page.load(); self.assertEqual(p.meta("og:image"), "https://lesovskiy.com/assets/og.jpg")
    self.assertEqual(jpeg_size(ROOT / "assets/og.jpg"), (1200, 630))

def test_jsonld_person(self):
    d = Page.load().jsonld[0]
    self.assertEqual((d["@type"], d["name"], d["alternateName"]), ("Person", "Vlad Lesovskiy", "Влад Лесовский"))
    self.assertIn("https://www.linkedin.com/in/vladles95", d["sameAs"])

def test_robots_and_sitemap(self):
    self.assertIn("Sitemap: https://lesovskiy.com/sitemap.xml", (ROOT / "robots.txt").read_text())
    ET.parse(ROOT / "sitemap.xml")  # well-formed
    self.assertIn("<loc>https://lesovskiy.com/</loc>", (ROOT / "sitemap.xml").read_text())
```

  Add helper `jpeg_size(path: Path) -> tuple[int, int]` to `tests/test_site.py`. It scans JPEG markers for SOF0–SOF15 (excluding `0xC4`, `0xC8` and `0xCC`) and reads height/width as big-endian u16 at offsets +5/+7 of the segment.

- [ ] **Step 2: Run the tests and confirm SeoTests fail.**
Run: `python3 -m unittest discover -s tests -v`
Expected: SeoTests FAIL. Everything else is OK.

- [ ] **Step 3: Add the `<head>` tags and create `robots.txt`, `sitemap.xml`, `tools/og.html`. Render `assets/og.jpg` with the commands above.**

- [ ] **Step 4: Run the tests and confirm all pass.**
Run: `python3 -m unittest discover -s tests -v`
Expected: OK.

- [ ] **Step 5: Validate.** Paste the JSON-LD block into https://validator.schema.org (expect 0 errors), and upload `index.html` to https://validator.w3.org/#validate_by_upload (expect 0 errors). Open `assets/og.jpg` and check that the text is crisp and nothing is clipped.

- [ ] **Step 6: Commit**

```bash
git add index.html robots.txt sitemap.xml tools/og.html assets/og.jpg tests/test_site.py
git commit -m "feat: SEO meta, Person structured data, sitemap and share image"
```

---

### Task 4: Update CLAUDE.md

**Files:**
- Create: `CLAUDE.md`. It exists only untracked in the main checkout. Write it fresh here, using the same header and sections as that one.

- [ ] **Step 1: Write `CLAUDE.md`** with:
  - The standard header.
  - Overview: unchanged facts (GitHub Pages, `CNAME`, push to `master` publishes).
  - Local preview: `python3 -m http.server 8000`.
  - Tests: `python3 -m unittest discover -s tests -v`, and how to run one test (`python3 -m unittest tests.test_site.SeoTests.test_jsonld_person`).
  - Structure: no framework; `assets/styles.css` uses CSS variables with a dark-mode override; `_config.yml` excludes internal files from Pages, so new internal files must be added there; `assets/og.jpg` is regenerated from `tools/og.html` with the Chrome + `sips` command from Task 3 whenever the name or title changes; the copy is kept in sync with the CV, which is gitignored and never published; and the Yandex tag must stay.

- [ ] **Step 2: Run the test suite.**
Run: `python3 -m unittest discover -s tests -v`
Expected: OK. `test_jekyll_excludes_internal_files` still passes, so CLAUDE.md stays unpublished.

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md for the redesigned site"
```

---

### Task 5: Final review in the browser and Lighthouse

**Files:** none, unless fixes come out of the review.

- [ ] **Step 1: Serve and show Vlad.** Run `python3 -m http.server 8000`, open http://localhost:8000, and show Vlad the page at 1280px and 375px in light and dark mode. Collect his changes and apply them. Rerun the tests after each change.

- [ ] **Step 2: Phone and contrast check.** At 320px the page has no horizontal scroll. In dark mode, check the contrast of body text, links and the Telegram button in DevTools' color picker (≥ 4.5:1).

- [ ] **Step 3: Lighthouse.**
Run: `npx -y lighthouse http://localhost:8000 --only-categories=performance,accessibility,best-practices,seo --quiet --chrome-flags="--headless" --output=json --output-path=/tmp/lh.json && python3 -c "import json;d=json.load(open('/tmp/lh.json'));print({k:round(v['score']*100) for k,v in d['categories'].items()})"`
Expected: every score ≥ 95. Fix anything lower, then rerun.

- [ ] **Step 4: Commit any fixes**

```bash
git add -A && git commit -m "fix: review feedback"
```

- [ ] **Step 5: After merge and deploy (with Vlad):**
  1. Check https://lesovskiy.com/ in Telegram (send the link to Saved Messages) and the LinkedIn Post Inspector.
  2. Google Rich Results Test on the live URL.
  3. Google Search Console: add the property, choose HTML-tag verification, and have Vlad paste the token. Add `<meta name="google-site-verification" content="…">` next to the Yandex tag, deploy, verify, then submit `sitemap.xml`.
  4. Before merging into the main checkout, delete or move its untracked `CLAUDE.md`. Otherwise git refuses to overwrite it.
