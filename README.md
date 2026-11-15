# The Digital Nook

An editorial-magazine blog: cover story, contents grid, Dispatches (notes), generated cover art per story, drop caps, pull quotes. Plain HTML from Markdown, hosted on Vercel.

- Write: add `content/YYYY-MM-DD-slug.md` (header: `title`, `date`, `summary`, `tags`; optional `type: note`, `draft: true`).
- Build: `python3 build.py` → `dist/` (posts at `/p/<slug>`, `/archive`, `/about`, `/feed.xml`, `/sitemap.xml`).
- Deploy: `cd dist && vercel deploy --prod --yes` (Vercel project `the-digital-nook`).

Reading mode on every post: `R` to toggle, `+`/`-` size, serif/sans, paper/white/dark; saved in the browser.
