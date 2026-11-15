# The Digital Nook

A minimal, tech-centred, very readable blog. Plain HTML from Markdown, hosted on Vercel.

- Write: add `content/YYYY-MM-DD-slug.md` (header: `title`, `date`, `summary`, `tags`; optional `type: note`, `draft: true`).
- Build: `python3 build.py` → `dist/` (posts at `/p/<slug>`, `/about`, `/feed.xml`, `/sitemap.xml`).
- Deploy: `cd dist && vercel deploy --prod --yes` (Vercel project `the-digital-nook`).

Reading mode on every post: `R` to toggle, `+`/`-` size, sans/serif, light/sepia/dark; saved in the browser.
