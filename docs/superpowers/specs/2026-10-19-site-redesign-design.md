# lesovskiy.com redesign — design

## Context

lesovskiy.com is currently a one-page bio built on Bulma. It has broken links: the header points to `lesovskiy.ru`, and the LinkedIn URL is missing `/in/`. It has no share previews and almost no SEO. Vlad wants to replace it with a new single page that presents him, using content from his CV (`Vlad_Lesovskiy_CV.pdf`, now in the repo root). The new page should be simple, modern and clear, and should be easier to find by name in search.

**Who it's for (Vlad):** HR people, HR leads and recruiters who search "Vlad Lesovskiy" to check him out.
**What success looks like (Vlad):** lesovskiy.com shows up for his name, the reader quickly sees him at his best, and then **messages him directly**.

## Goals
- Rank lesovskiy.com first for "Vlad Lesovskiy".
- A recruiter understands within ~30 seconds who he is, what he has built, and how to reach him.
- Contacting him is obvious. Telegram is the primary action.
- Share previews (Telegram, LinkedIn, Slack) show his name, title and photo.

## Non-goals
- No Russian version (Vlad: English only).
- No blog, multiple pages, project gallery or animations.
- The CV PDF is not published (Vlad: keep private).

## Anti-goals (failure even if it "works")
- Flashy or "special" design. Vlad: "simple, clear for visitors and show me from the best side".
- A page that just copies the whole CV. It should make the reader want to talk, not replace the conversation.

## Constraints
- Static GitHub Pages site from `master`. Custom domain via `CNAME` (`lesovskiy.com`). No build step.
- Keep the Yandex verification meta tag (`691bad7d13005913`).
- Keep `assets/avatar.jpg` as the photo.

## Decided with Vlad
- One page, English only.
- Content comes from the CV.
- Main call to action: message directly (Telegram, then email and LinkedIn).
- Look: simple and clear, inspired by brandoncjohnson.com (Open Sans, stacked "contact card" footer: name, role, location, email) and 1chooo.com (Fraunces serif headings, narrow single column, one-line "places" footer).
- CV PDF stays private: add `Vlad_Lesovskiy_CV.pdf` to `.gitignore`.
- Iterate in words; the final result is shown in the browser for review before committing.
- Availability: say he's **open to offers**, in one quiet line in the intro ("Open to new opportunities") and in the meta and OG description. No specific terms.
- Name forms: only "Vlad Lesovskiy" and "Влад Лесовский". Don't invent a formal first name.
- Google Search Console is not set up. After deploy, give Vlad the steps (add property → HTML-tag verification → he pastes the token → add the meta tag → submit `sitemap.xml`).

## Page content (proposed, played back without objection)
1. **Intro:** small round avatar (shown on every screen size), `<h1>` "Vlad Lesovskiy", "Lead Software Engineer · Belgrade, Serbia", 2–3 sentences condensed from the CV summary, and a primary **"Message me on Telegram"** button (`https://t.me/vladles`) plus a secondary email link.
2. **Experience:** MaxRx (Jun 2025–present), CharityRx (Jan 2020–Jan 2026), Pix Wireless (Jan 2018–Aug 2023), and "Earlier": CimpleO 2017–2019 and WordPress Monsters 2016–2017. Each role has dates, a one-line product description and 2–3 of the strongest results (e.g. MVP in 5 months; 2 medical providers integrated through a state machine; React Native apps shipped to both stores; Next.js migration for SEO; MVNO integrations with 3 operators; 10-person team and hiring). Leave out the CV's draft-like "I started as WordPress developer…" paragraph.
3. **Skills:** the six CV groups as compact label + line rows (Backend & data, Frontend & mobile, Cloud & delivery, Integrations, Architecture & leadership, AI-assisted engineering).
4. **Education & languages:** one line. BSc Applied Mathematics and Physics, Omsk State University · Russian (native), English (B2).
5. **Outside work:** 2 short lines in Vlad's current voice: volunteer organizer at vas3k events (100+ people), sailing and charters, helping newcomers.
6. **Contact card footer:** "Vlad Lesovskiy / Lead Software Engineer / Belgrade, Serbia", then Telegram, inbox@lesovskiy.com, LinkedIn `https://www.linkedin.com/in/vladles95`, GitHub `https://github.com/vladles`.

## SEO
- `<title>`: "Vlad Lesovskiy — Lead Software Engineer". Meta description of about 150 characters naming his stack and domains.
- `<link rel="canonical" href="https://lesovskiy.com/">`, `lang="en"`, semantic landmarks (`header`/`main`/`section`/`footer`), a single `h1`.
- Open Graph and Twitter tags: title, description, URL, `og:image` = absolute URL of a 1200×630 share image, `og:type=profile`.
- JSON-LD `Person`: name, `alternateName: "Влад Лесовский"`, jobTitle, `address` (Belgrade, RS), email, url, image, `sameAs` (LinkedIn, GitHub, Telegram), `alumniOf` Omsk State University, `knowsAbout` (core stack).
- `robots.txt` (allow all, point to the sitemap) and a one-URL `sitemap.xml`.
- Performance: no JS and no CSS framework, explicit `width`/`height` on images, `preconnect` + `display=swap` for fonts.

## Builder's calls (Claude's, not agreed with Vlad; easy to veto)
- Drop Bulma; write a small hand-written `assets/styles.css` (CSS variables, about 150 lines).
- Fonts: **Fraunces** for the name and section headings, **Open Sans** for body text (one font from each reference), from Google Fonts.
- Light theme by default plus automatic dark mode via `prefers-color-scheme`.
- Narrow column (~680px max) with generous spacing; sections separated by space and small uppercase labels, not boxes.
- Drop the `lesovskiy.ru` header link entirely.
- Share image: `assets/og.jpg`, 1200×630, generated once locally from the avatar plus name and title (a committed static file, not built at runtime).
- Favicon: a small SVG monogram "VL" in the accent color.
- Update `CLAUDE.md` afterwards (no Bulma; new files).

## Files
- Rewrite: `index.html`, `assets/styles.css`
- Add: `robots.txt`, `sitemap.xml`, `assets/og.jpg`, `assets/favicon.svg`
- Edit: `.gitignore` (add the CV PDF), `CLAUDE.md`

## Verification
1. `python3 -m http.server 8000`, then open http://localhost:8000 in the browser and show Vlad the result at desktop and phone widths, in light and dark mode.
2. Check every link (Telegram, mailto, LinkedIn `/in/vladles95`, GitHub).
3. Validate the HTML (W3C validator) and the JSON-LD (schema.org validator). After deploy, run Google Rich Results Test and the Telegram/LinkedIn post inspector on https://lesovskiy.com/.
4. Run Lighthouse (SEO, accessibility, performance) and aim for 95+ on each.
5. `git status` confirms the CV PDF is ignored.
6. After deploy: Search Console verification and sitemap submission with Vlad's token (see "Decided with Vlad").
