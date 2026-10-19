# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Single-page personal site for Vlad Lesovskiy, aimed at recruiters who search his name. It's served by GitHub Pages from the `master` branch at the custom domain in `CNAME` (`lesovskiy.com`). There is no build step and no package manager: what is committed is what gets deployed, and pushing to `master` publishes.

## Commands

```sh
python3 -m http.server 8000                    # local preview at http://localhost:8000
python3 -m unittest discover -s tests -v       # all checks
python3 -m unittest tests.test_site.SeoTests.test_jsonld_person   # one test
```

Asset paths are root-relative (`/assets/...`), so opening `index.html` via `file://` breaks styles and images. Always preview through the server.

## How it fits together

- `index.html` is the whole site: intro + Telegram CTA, experience, skills, education, outside work, and a contact-card footer. Its `<head>` carries all SEO: title/description, canonical, Open Graph/Twitter tags, and a JSON-LD `Person` block. The title, description and name forms are pinned by `tests/test_site.py`, so change the tests together with the copy.
- `assets/styles.css` is hand-written (no framework). Colors are CSS variables on `:root`, redefined under `@media (prefers-color-scheme: dark)`. Fonts are Fraunces (headings) and Open Sans (body) from Google Fonts.
- `_config.yml` excludes `docs`, `tests`, `tools`, `CLAUDE.md` and `README.md` from the published site. GitHub Pages runs Jekyll, which would otherwise publish them. **Add any new internal file or folder there.**
- `assets/og.jpg` (1200×630 share image) is generated from `tools/og.html`. Rerun the Chrome + `sips` command in that file's header comment whenever the name or title changes.
- `robots.txt` and `sitemap.xml` point search engines to the single URL. Bump `<lastmod>` when content changes.

## Content rules

- Copy comes from Vlad's CV (`Vlad_Lesovskiy_CV.pdf`). It is gitignored and must never be committed or linked.
- English only. Name forms are exactly "Vlad Lesovskiy" and, in JSON-LD only, "Влад Лесовский". Don't invent a formal first name.
- Keep the `yandex-verification` meta tag.
- `docs/superpowers/` holds the redesign spec and plan.
