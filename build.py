"""The Digital Nook — builds the static site from content/*.md into dist/.

A post is content/YYYY-MM-DD-slug.md with a header:
    ---
    title: ...
    date: 2026-10-12
    summary: one sentence for the list and link previews
    tags: engineering, release
    type: note          (optional: a short entry shown in full on the home page)
    draft: true         (optional: leave it off the site)
    ---
Markdown: ## / ### headings, paragraphs, - and 1. lists, ``` code (```lang), **bold**, *italic*, `code`,
[links](url), ![images](url), and "> **Label:** text" callouts.

Run: python3 build.py            (SITE_URL=https://… to set the canonical address)
"""
import glob, html, os, re, shutil
from datetime import date, datetime, timezone
from email.utils import format_datetime

NAME = "The Digital Nook"
TAGLINE = "Notes from building software in public. Bugs, measurements and decisions, written down as they happen."
SITE = os.environ.get("SITE_URL", "https://the-digital-nook.vercel.app").rstrip("/")
ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "dist")

# ---------- Markdown ----------
def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)", r'<img src="\2" alt="\1" loading="lazy">', s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?!\w)", r"<em>\1</em>", s)
    return s

def slugify(s): return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

def markdown(text):
    out, toc, para, lst, code, lang = [], [], [], None, None, ""
    def flush():
        nonlocal para, lst
        if para: out.append("<p>" + inline(" ".join(para)) + "</p>"); para = []
        if lst: out.append(f"<{lst[0]}>" + "".join(f"<li>{inline(i)}</li>" for i in lst[1]) + f"</{lst[0]}>"); lst = None
    for line in text.splitlines():
        if code is not None:
            if line.startswith("```"):
                label = f'<span class="lang">{html.escape(lang)}</span>' if lang else ""
                out.append(f'<div class="code">{label}<button class="copy" type="button">copy</button><pre><code>' + html.escape("\n".join(code)) + "</code></pre></div>")
                code = None
            else: code.append(line)
            continue
        if line.startswith("```"): flush(); code, lang = [], line[3:].strip(); continue
        m = re.match(r"(#{2,4})\s+(.*)", line)
        if m:
            flush(); n = len(m.group(1)); hid = slugify(m.group(2))
            if n == 2: toc.append((hid, m.group(2)))
            out.append(f'<h{n} id="{hid}"><a class="anchor" href="#{hid}" aria-hidden="true">#</a>{inline(m.group(2))}</h{n}>'); continue
        m = re.match(r"\s*([-*]|\d+\.)\s+(.*)", line)
        if m:
            if para: flush()
            kind = "ul" if m.group(1) in "-*" else "ol"
            if not lst or lst[0] != kind: flush(); lst = (kind, [])
            lst[1].append(m.group(2)); continue
        if line.startswith(">"): flush(); out.append('<aside class="callout"><p>' + inline(line.lstrip("> ")) + "</p></aside>"); continue
        if not line.strip(): flush(); continue
        if lst: flush()
        para.append(line.strip())
    flush()
    return "\n".join(out), toc

# ---------- Look ----------
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&display=swap">')

CSS = r"""
:root {
  --bg: #fbfbfa; --fg: #16181a; --text: #2a2d31; --muted: #6b7076; --line: #e6e7e8; --soft: #f2f3f3;
  --accent: #2f6fed; --accent-soft: #e8effd; --code-bg: #f4f5f6;
  --sans: "IBM Plex Sans", system-ui, -apple-system, sans-serif; --mono: "IBM Plex Mono", ui-monospace, Menlo, monospace; --serif: "Newsreader", Georgia, serif;
  --read: var(--sans); --size: 19px; --measure: 68ch;
  color-scheme: light;
}
html[data-theme="sepia"] { --bg: #f6f0e4; --fg: #2b2216; --text: #3b3022; --muted: #7c6c55; --line: #e4d9c4; --soft: #efe6d4; --accent: #9a5b13; --accent-soft: #f0e2c8; --code-bg: #efe6d4; }
html[data-theme="dark"] { --bg: #111315; --fg: #eceef0; --text: #cfd3d7; --muted: #8a9096; --line: #26292d; --soft: #1a1d20; --accent: #7aa7ff; --accent-soft: #1b2638; --code-bg: #181b1e; color-scheme: dark; }
html[data-font="serif"] { --read: var(--serif); }
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; scroll-padding-top: 24px; }
body { margin: 0; background: var(--bg); color: var(--text); font: 400 17px/1.6 var(--sans); -webkit-font-smoothing: antialiased; }
a { color: inherit; }
::selection { background: var(--accent-soft); }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; border-radius: 3px; }
.wrap { max-width: 760px; margin: 0 auto; padding: 0 24px; }
.mono { font-family: var(--mono); }

/* top bar */
.top { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 26px 0; }
.logo { font: 500 .95rem/1 var(--mono); color: var(--fg); text-decoration: none; letter-spacing: -.01em; }
.logo .p { color: var(--accent); }
.logo .cur { display: inline-block; width: .55em; height: 1.05em; margin-left: 3px; vertical-align: -2px; background: var(--accent); animation: blink 1.1s steps(1) infinite; }
@keyframes blink { 50% { opacity: 0; } }
.top nav { display: flex; gap: 20px; font: 400 .85rem var(--mono); }
.top nav a { color: var(--muted); text-decoration: none; }
.top nav a:hover { color: var(--fg); }

/* home */
.hero { padding: clamp(48px, 10vw, 112px) 0 40px; }
.hero h1 { font: 600 clamp(2.2rem, 6vw, 3.4rem)/1.08 var(--sans); letter-spacing: -.035em; color: var(--fg); margin: 0; }
.hero p { font-size: 1.15rem; color: var(--muted); max-width: 36em; margin: 18px 0 0; }
.label { font: 500 .74rem/1 var(--mono); letter-spacing: .06em; color: var(--muted); text-transform: lowercase; }
.label::before { content: "// "; color: var(--accent); }
.posts { list-style: none; margin: 18px 0 0; padding: 0; border-top: 1px solid var(--line); }
.posts li { border-bottom: 1px solid var(--line); }
.posts a.row { display: grid; grid-template-columns: 104px 1fr; gap: 20px; padding: 22px 0; text-decoration: none; }
.posts time { font: 400 .82rem/1.9 var(--mono); color: var(--muted); }
.posts h2 { font: 600 1.28rem/1.3 var(--sans); letter-spacing: -.015em; color: var(--fg); margin: 0 0 6px; }
.posts a.row:hover h2 { color: var(--accent); }
.posts p { margin: 0; color: var(--muted); font-size: 1rem; line-height: 1.55; }
.posts .tags { margin-top: 8px; font: 400 .76rem var(--mono); color: var(--muted); }
.posts .note { display: grid; grid-template-columns: 104px 1fr; gap: 20px; padding: 20px 0; }
.posts .note .k { font: 500 .72rem var(--mono); color: var(--accent); display: block; margin-top: 2px; }
.posts .note h3 { font: 600 1rem/1.4 var(--sans); color: var(--fg); margin: 0 0 4px; }
.posts .note p { color: var(--text); font-size: .98rem; }
.posts code, article :not(pre) > code { font: .86em var(--mono); background: var(--code-bg); border: 1px solid var(--line); padding: 1px 5px; border-radius: 4px; }

/* post */
.progress { position: fixed; inset: 0 0 auto 0; height: 2px; background: var(--accent); transform-origin: 0 50%; transform: scaleX(0); z-index: 20; }
.post-head { padding: clamp(36px, 8vw, 80px) 0 28px; }
.post-head h1 { font: 600 clamp(2rem, 5.5vw, 3rem)/1.1 var(--sans); letter-spacing: -.03em; color: var(--fg); margin: 14px 0 0; text-wrap: balance; }
.post-head .sub { font-size: 1.15rem; color: var(--muted); margin: 16px 0 0; }
.meta { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 14px; font: 400 .8rem var(--mono); color: var(--muted); margin-top: 22px; padding-top: 18px; border-top: 1px solid var(--line); }
.meta .sp { flex: 1; }
.btn { font: 500 .8rem var(--mono); color: var(--fg); background: var(--soft); border: 1px solid var(--line); border-radius: 6px; padding: 7px 11px; cursor: pointer; display: inline-flex; align-items: center; gap: 7px; }
.btn:hover { border-color: var(--muted); }
.btn kbd { font: inherit; font-size: .7rem; color: var(--muted); border: 1px solid var(--line); border-radius: 3px; padding: 0 4px; }

article { font: 400 var(--size)/1.75 var(--read); color: var(--text); max-width: var(--measure); padding-bottom: 8px; }
html[data-font="serif"] article { line-height: 1.7; }
article p { margin: 0 0 1.3em; }
article h2 { font: 600 1.45em/1.25 var(--sans); letter-spacing: -.02em; color: var(--fg); margin: 2em 0 .55em; position: relative; }
article h3 { font: 600 1.12em/1.3 var(--sans); color: var(--fg); margin: 1.7em 0 .4em; position: relative; }
article .anchor { position: absolute; left: -1.1em; color: var(--muted); text-decoration: none; opacity: 0; font-family: var(--mono); font-weight: 400; }
article h2:hover .anchor, article h3:hover .anchor { opacity: 1; }
article ul, article ol { padding-left: 1.25em; margin: 0 0 1.3em; }
article li { margin: .35em 0; }
article li::marker { color: var(--muted); }
article a { color: var(--accent); text-underline-offset: 3px; text-decoration-thickness: 1px; }
article strong { color: var(--fg); font-weight: 600; }
article img { max-width: 100%; border-radius: 8px; border: 1px solid var(--line); }
.callout { border-left: 3px solid var(--accent); background: var(--accent-soft); border-radius: 0 8px 8px 0; padding: 14px 18px; margin: 1.8em 0; }
.callout p { margin: 0; }
.code { position: relative; margin: 1.6em 0; border: 1px solid var(--line); border-radius: 8px; background: var(--code-bg); }
.code pre { margin: 0; overflow-x: auto; padding: 16px 18px; font: 400 .84rem/1.65 var(--mono); color: var(--fg); }
.code .lang { position: absolute; left: 14px; top: -9px; font: 500 .68rem var(--mono); color: var(--muted); background: var(--bg); padding: 0 6px; }
.code .copy { position: absolute; right: 8px; top: 8px; font: 500 .7rem var(--mono); color: var(--muted); background: var(--bg); border: 1px solid var(--line); border-radius: 4px; padding: 3px 7px; cursor: pointer; opacity: 0; transition: opacity .15s; }
.code:hover .copy, .copy:focus-visible { opacity: 1; }
.after { margin: 56px 0 0; padding: 24px 0 0; border-top: 1px solid var(--line); display: grid; gap: 4px; }
.after a { text-decoration: none; }
.after b { font: 600 1.15rem/1.35 var(--sans); color: var(--fg); }
.after a:hover b { color: var(--accent); }

footer { margin-top: 80px; padding: 24px 0 44px; border-top: 1px solid var(--line); display: flex; flex-wrap: wrap; justify-content: space-between; gap: 10px; font: 400 .8rem var(--mono); color: var(--muted); }
footer a { color: var(--muted); text-decoration: none; } footer a:hover { color: var(--fg); }

/* reading mode: just the words */
.rbar { display: none; }
html.reading .top, html.reading footer, html.reading .after, html.reading .meta .btn-read { display: none; }
html.reading .wrap { max-width: calc(var(--measure) + 48px); }
html.reading .post-head { padding-top: 88px; }
html.reading .rbar { display: flex; position: fixed; top: 12px; left: 50%; transform: translateX(-50%); z-index: 30; gap: 4px; align-items: center; padding: 5px; border: 1px solid var(--line); border-radius: 10px; background: color-mix(in srgb, var(--bg) 88%, transparent); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); box-shadow: 0 6px 24px -12px rgba(0,0,0,.25); transition: opacity .25s; }
html.reading.idle .rbar { opacity: 0; }
html.reading.idle .rbar:hover, html.reading .rbar:focus-within { opacity: 1; }
.rbar button { font: 500 .78rem var(--mono); color: var(--fg); background: none; border: 0; border-radius: 6px; padding: 7px 9px; cursor: pointer; min-width: 32px; }
.rbar button:hover { background: var(--soft); }
.rbar button[aria-pressed="true"] { background: var(--soft); color: var(--accent); }
.rbar .sep { width: 1px; height: 18px; background: var(--line); margin: 0 3px; }
.rbar .sw { width: 14px; height: 14px; border-radius: 50%; display: inline-block; vertical-align: -2px; border: 1px solid rgba(0,0,0,.2); }

@media (max-width: 600px) {
  body { font-size: 16px; } :root { --size: 18px; }
  .posts a.row, .posts .note { grid-template-columns: 1fr; gap: 4px; }
  .top nav { gap: 14px; }
  article .anchor { display: none; }
  html.reading .rbar { top: auto; bottom: 14px; }
  html.reading .post-head { padding-top: 40px; }
  .rbar .hide-sm { display: none; }
}
@media (prefers-reduced-motion: reduce) { *, .logo .cur { animation: none !important; transition: none !important; } }
"""

# Applied before paint so a saved reader theme never flashes.
BOOT = """<script>try{var s=JSON.parse(localStorage.getItem('nook-reader')||'{}'),d=document.documentElement;if(s.theme)d.dataset.theme=s.theme;if(s.font)d.dataset.font=s.font;if(s.size)d.style.setProperty('--size',s.size+'px');if(s.on&&location.pathname.split('/').length>2)d.classList.add('reading')}catch(e){}</script>"""

POST_JS = r"""<script>
(() => {
  const d = document.documentElement, KEY = 'nook-reader';
  const load = () => { try { return JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) { return {}; } };
  const save = s => { try { localStorage.setItem(KEY, JSON.stringify(s)); } catch (e) {} };
  let s = load();
  const base = () => parseFloat(getComputedStyle(d).getPropertyValue('--size')) || 19;
  const sync = () => {
    document.querySelectorAll('[data-theme-set]').forEach(b => b.setAttribute('aria-pressed', (d.dataset.theme || 'light') === b.dataset.themeSet));
    document.querySelectorAll('[data-font-set]').forEach(b => b.setAttribute('aria-pressed', (d.dataset.font || 'sans') === b.dataset.fontSet));
    const r = document.querySelector('.btn-read'); if (r) r.setAttribute('aria-pressed', d.classList.contains('reading'));
  };
  const toggle = on => { on = on ?? !d.classList.contains('reading'); d.classList.toggle('reading', on); s.on = on; save(s); sync(); if (on) idle(); };
  document.querySelectorAll('[data-read]').forEach(b => b.addEventListener('click', () => toggle()));
  document.querySelectorAll('[data-theme-set]').forEach(b => b.addEventListener('click', () => { const t = b.dataset.themeSet; if (t === 'light') delete d.dataset.theme; else d.dataset.theme = t; s.theme = t === 'light' ? '' : t; save(s); sync(); }));
  document.querySelectorAll('[data-font-set]').forEach(b => b.addEventListener('click', () => { const f = b.dataset.fontSet; if (f === 'sans') delete d.dataset.font; else d.dataset.font = f; s.font = f === 'sans' ? '' : f; save(s); sync(); }));
  document.querySelectorAll('[data-size]').forEach(b => b.addEventListener('click', () => { const n = Math.min(26, Math.max(15, base() + +b.dataset.size)); d.style.setProperty('--size', n + 'px'); s.size = n; save(s); }));
  addEventListener('keydown', e => {
    if (e.metaKey || e.ctrlKey || e.altKey || /input|textarea/i.test(e.target.tagName)) return;
    if (e.key === 'r') toggle(); else if (e.key === 'Escape' && d.classList.contains('reading')) toggle(false);
    else if (d.classList.contains('reading') && (e.key === '+' || e.key === '=')) document.querySelector('[data-size="1"]').click();
    else if (d.classList.contains('reading') && e.key === '-') document.querySelector('[data-size="-1"]').click();
  });
  // In reading mode the toolbar fades out while you read and comes back when you move.
  let t; const idle = () => { d.classList.remove('idle'); clearTimeout(t); t = setTimeout(() => d.classList.contains('reading') && d.classList.add('idle'), 2200); };
  ['mousemove', 'touchstart', 'keydown'].forEach(ev => addEventListener(ev, idle, { passive: true }));
  // progress
  const bar = document.querySelector('.progress'), art = document.querySelector('article');
  const tick = () => { const r = art.getBoundingClientRect(); bar.style.transform = `scaleX(${Math.min(1, Math.max(0, -r.top / Math.max(r.height - innerHeight * .6, 1)))})`; };
  addEventListener('scroll', tick, { passive: true }); tick();
  // copy buttons
  document.querySelectorAll('.code .copy').forEach(b => b.addEventListener('click', async () => {
    try { await navigator.clipboard.writeText(b.parentElement.querySelector('code').innerText); b.textContent = 'copied'; } catch (e) { b.textContent = 'press ⌘C'; }
    setTimeout(() => b.textContent = 'copy', 1400); }));
  sync(); if (d.classList.contains('reading')) idle();
})();
</script>"""

def page(title, desc, path, body, script=""):
    t, dsc = html.escape(title), html.escape(desc)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{t}</title>
<meta name="description" content="{dsc}">
<meta property="og:title" content="{t}"><meta property="og:description" content="{dsc}"><meta property="og:site_name" content="{NAME}">
<meta name="twitter:card" content="summary">
<meta name="theme-color" content="#fbfbfa">
<link rel="canonical" href="{SITE}{path}">
<link rel="alternate" type="application/rss+xml" title="{NAME}" href="/feed.xml">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
{BOOT}
{FONTS}
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
<header class="top"><a class="logo" href="/" aria-label="{NAME}, home"><span class="p">~/</span>the-digital-nook<span class="cur" aria-hidden="true"></span></a>
<nav><a href="/">posts</a><a href="/about">about</a><a href="/feed.xml">rss</a></nav></header>
{body}
<footer><span>© {date.today().year} {NAME}</span><span>plain html · no trackers · <a href="/feed.xml">rss</a></span></footer>
</div>
{script}
</body>
</html>
"""

# ---------- Build ----------
iso = lambda d: d.isoformat()
nice = lambda d: d.strftime("%b %-d, %Y")
posts = []
for f in sorted(glob.glob(os.path.join(ROOT, "content", "*.md"))):
    m = re.match(r"---\n(.*?)\n---\n(.*)", open(f).read(), re.S)
    if not m: raise SystemExit(f"✗ {f}: missing --- header")
    meta = {k.strip(): v.strip() for k, v in (l.split(":", 1) for l in m.group(1).splitlines() if ":" in l)}
    if meta.get("draft") == "true": continue
    body, toc = markdown(m.group(2))
    words = len(re.sub(r"<[^>]+>", " ", body).split())
    posts.append(dict(slug=re.sub(r"^\d{4}-\d{2}-\d{2}-", "", os.path.basename(f)[:-3]), title=meta["title"],
                      date=date.fromisoformat(meta["date"]), summary=meta.get("summary", ""), note=meta.get("type") == "note",
                      tags=[t.strip() for t in meta.get("tags", "").split(",") if t.strip()], body=body, words=words,
                      mins=max(1, round(words / 220))))
posts.sort(key=lambda p: (p["date"], p["slug"]), reverse=True)
essays = [p for p in posts if not p["note"]]

if os.path.isdir(OUT):
    for x in os.listdir(OUT):
        if x != ".vercel": shutil.rmtree(os.path.join(OUT, x)) if os.path.isdir(os.path.join(OUT, x)) else os.remove(os.path.join(OUT, x))
os.makedirs(os.path.join(OUT, "p"), exist_ok=True)

READBAR = """<div class="rbar" role="toolbar" aria-label="Reading settings">
  <button type="button" data-size="-1" aria-label="Smaller text">A−</button><button type="button" data-size="1" aria-label="Larger text">A+</button>
  <span class="sep"></span>
  <button type="button" data-font-set="sans">Sans</button><button type="button" data-font-set="serif">Serif</button>
  <span class="sep"></span>
  <button type="button" data-theme-set="light" aria-label="Light"><span class="sw" style="background:#fbfbfa"></span></button><button type="button" data-theme-set="sepia" aria-label="Sepia"><span class="sw" style="background:#f6f0e4"></span></button><button type="button" data-theme-set="dark" aria-label="Dark"><span class="sw" style="background:#111315"></span></button>
  <span class="sep"></span>
  <button type="button" data-read aria-label="Leave reading mode">✕<span class="hide-sm">&nbsp;exit</span></button>
</div>"""

for i, p in enumerate(essays):
    older = essays[i + 1] if i + 1 < len(essays) else None
    after = (f'<nav class="after"><span class="label">previous</span><a href="/p/{older["slug"]}"><b>{html.escape(older["title"])}</b></a></nav>' if older
             else '<nav class="after"><span class="label">that\'s the first one</span><a href="/"><b>All posts →</b></a></nav>')
    tagline = " ".join(f"#{html.escape(t)}" for t in p["tags"])
    body = f"""<div class="progress" aria-hidden="true"></div>
{READBAR}
<main>
  <header class="post-head">
    <span class="label">{iso(p["date"])}</span>
    <h1>{html.escape(p["title"])}</h1>
    {f'<p class="sub">{html.escape(p["summary"])}</p>' if p["summary"] else ""}
    <div class="meta"><span>{p["mins"]} min read</span><span>{p["words"]} words</span><span>{tagline}</span><span class="sp"></span>
      <button class="btn btn-read" type="button" data-read aria-pressed="false">reading mode <kbd>R</kbd></button></div>
  </header>
  <article>
{p["body"]}
  </article>
  {after}
</main>"""
    open(os.path.join(OUT, "p", p["slug"] + ".html"), "w").write(page(f'{p["title"]} — {NAME}', p["summary"], f'/p/{p["slug"]}', body, POST_JS))

def row(p):
    if p["note"]:
        return f'  <li class="note" id="{p["slug"]}"><div><time class="mono" datetime="{iso(p["date"])}" style="font-size:.82rem;color:var(--muted)">{nice(p["date"])}</time><span class="k">note</span></div><div><h3>{html.escape(p["title"])}</h3>{p["body"]}</div></li>'
    tags = " ".join(f"#{html.escape(t)}" for t in p["tags"])
    return f'  <li><a class="row" href="/p/{p["slug"]}"><time datetime="{iso(p["date"])}">{nice(p["date"])}</time><div><h2>{html.escape(p["title"])}</h2><p>{html.escape(p["summary"])}</p><div class="tags">{p["mins"]} min · {tags}</div></div></a></li>'

home = f"""<main>
  <section class="hero">
    <h1>{NAME}</h1>
    <p>{TAGLINE}</p>
  </section>
  <span class="label">posts &amp; notes</span>
  <ul class="posts">
{chr(10).join(row(p) for p in posts)}
  </ul>
</main>"""
open(os.path.join(OUT, "index.html"), "w").write(page(NAME, TAGLINE, "/", home))

about = f"""<main>
  <header class="post-head"><span class="label">about</span><h1>A small corner for the work behind the work.</h1></header>
  <article>
<p>{NAME} is where I write down what happens while building software: the bugs that took too long to find, the numbers behind each decision, and the things still undecided.</p>
<p>Right now most of it is about <a href="https://freshflo.vercel.app">Freshflo</a>, a dictation app for Mac, Windows and Android, on its way to launch.</p>
<h2 id="how">How this site is made</h2>
<p>Plain HTML generated from Markdown files by one small Python script, hosted on Vercel. No trackers, no cookies, no JavaScript you need to read a post.</p>
<p>Every post has a <strong>reading mode</strong>: press <code>R</code> to hide everything but the words, then pick text size, sans or serif, and a light, sepia or dark page. It remembers your choice.</p>
<p>Follow along with the <a href="/feed.xml">RSS feed</a>.</p>
  </article>
</main>"""
open(os.path.join(OUT, "about.html"), "w").write(page(f"About — {NAME}", "What The Digital Nook is and how it's made.", "/about", about))

open(os.path.join(OUT, "404.html"), "w").write(page(f"Not found — {NAME}", "Page not found.", "/404", '<main><section class="hero"><span class="label">404</span><h1>Nothing in this nook.</h1><p><a href="/">← back to all posts</a></p></section></main>'))

open(os.path.join(OUT, "favicon.svg"), "w").write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="7" fill="#16181a"/><path d="M8 11l6 5-6 5" fill="none" stroke="#fbfbfa" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/><rect x="16" y="20" width="9" height="2.8" rx="1" fill="#2f6fed"/></svg>')

rfc = lambda d: format_datetime(datetime(d.year, d.month, d.day, tzinfo=timezone.utc))
link = lambda p: f"{SITE}/#{p['slug']}" if p["note"] else f"{SITE}/p/{p['slug']}"
items = "\n".join(f"  <item><title>{html.escape(p['title'])}</title><link>{link(p)}</link><guid>{link(p)}</guid><pubDate>{rfc(p['date'])}</pubDate><description>{html.escape(p['summary'] or re.sub(r'<[^>]+>', '', p['body']))}</description></item>" for p in posts)
open(os.path.join(OUT, "feed.xml"), "w").write(f'<?xml version="1.0" encoding="utf-8"?>\n<rss version="2.0"><channel>\n  <title>{NAME}</title><link>{SITE}</link><description>{html.escape(TAGLINE)}</description>\n{items}\n</channel></rss>\n')
open(os.path.join(OUT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
urls = ["/", "/about"] + [f"/p/{p['slug']}" for p in essays]
open(os.path.join(OUT, "sitemap.xml"), "w").write('<?xml version="1.0" encoding="utf-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(f"  <url><loc>{SITE}{u}</loc></url>" for u in urls) + "\n</urlset>\n")
shutil.copy(os.path.join(ROOT, "vercel.json"), os.path.join(OUT, "vercel.json"))
print(f"✓ {NAME}: {len(essays)} posts, {len(posts) - len(essays)} notes → dist/")
