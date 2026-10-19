# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Single-page personal site for Vlad Lesovskiy, served by GitHub Pages from the `master` branch at the custom domain in `CNAME` (`lesovskiy.com`). There is no build step, package manager, linter, or test suite: what is committed is what gets deployed, and pushing to `master` publishes.

## Local preview

Asset paths are root-relative (`/assets/...`), so opening `index.html` directly via `file://` breaks the stylesheet and avatar. Serve the repo root instead:

```sh
python3 -m http.server 8000   # then open http://localhost:8000
```

## Structure

- `index.html` — the entire site: header (`@vladles` nickname link), bio, contact links, avatar column, footer.
- `assets/styles.css` — small set of overrides on top of Bulma.
- Styling uses **Bulma 0.9.4** loaded from jsDelivr; layout relies on Bulma classes (`container`, `columns`, `column is-three-quarters`, `is-hidden-touch`, `content is-medium`). Prefer Bulma utility classes before adding custom CSS.
- Custom CSS details worth knowing: the footer is `position: absolute` at the bottom of a `100vh` body, and the `.nickname` underline/`@` prefix are drawn with `::before`/`::after` pseudo-elements. The avatar column is hidden below 1024px (`is-hidden-touch`), matching the `max-width: 1023px` media query in `styles.css`.
- `<head>` contains a Yandex site-verification meta tag; keep it.
