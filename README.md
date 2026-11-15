# The Digital Nook

Freshflo's behind-the-scenes journal, told as a story: Freshflo brand (logo, pearl/ink/mint, Instrument Serif), animated logo hero, chapter timeline along the brand line, stories as numbered chapters, dispatches, Try Freshflo call to action. Plain HTML from Markdown, hosted on Vercel.

- Story timeline and launch checklist: `content/_story.json` (milestones; roadmap status done / doing / todo).
- Brand files: `static/` (copied from Freshflo-Website/brand and assets).

- Write: add `content/YYYY-MM-DD-slug.md` (header: `title`, `date`, `summary`, `tags`; optional `type: note`, `draft: true`).
- Build: `python3 build.py` → `dist/` (posts at `/p/<slug>`, `/archive`, `/about`, `/feed.xml`, `/sitemap.xml`).
- Deploy: `cd dist && vercel deploy --prod --yes` (Vercel project `the-digital-nook`).

Reading mode on every post: `R` to toggle, `+`/`-` size, sans/serif, light/sepia/dark; saved in the browser.
