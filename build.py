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

# ---------- Look: an editorial magazine on warm paper ----------
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,800;1,600;1,800&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap">')

CSS = r"""
:root {
  --paper: #f4ede1; --paper-2: #ebe2d2; --ink: #121110; --text: #2b2723; --muted: #6f665c; --rule: #d6cbb8; --red: #a3261b; --red-soft: #f1ddd2;
  --display: "Playfair Display", Georgia, serif; --serif: "Newsreader", Georgia, serif; --ui: "Inter", system-ui, -apple-system, sans-serif; --mono: "JetBrains Mono", ui-monospace, Menlo, monospace;
  --read: var(--serif); --size: 21px; --measure: 64ch; color-scheme: light;
}
html[data-theme="white"] { --paper: #fdfcfa; --paper-2: #f2f0ec; --rule: #e3dfd8; }
html[data-theme="dark"] { --paper: #16140f; --paper-2: #1f1c16; --ink: #f1ebe0; --text: #d8d0c3; --muted: #9d9385; --rule: #36302a; --red: #ef7b6a; --red-soft: #3a211c; color-scheme: dark; }
html[data-font="sans"] { --read: var(--ui); }
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; scroll-padding-top: 24px; }
body { margin: 0; background: var(--paper); color: var(--text); font: 400 16px/1.6 var(--ui); -webkit-font-smoothing: antialiased; }
a { color: inherit; }
::selection { background: var(--red-soft); }
:focus-visible { outline: 2px solid var(--red); outline-offset: 3px; }
.wrap { max-width: 1200px; margin: 0 auto; padding: 0 clamp(18px, 4vw, 48px); }
.kicker { font: 500 .7rem/1.4 var(--mono); letter-spacing: .16em; text-transform: uppercase; color: var(--red); }
.small { font: 500 .72rem/1.4 var(--ui); letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }

/* strip + masthead */
.strip { background: var(--ink); color: var(--paper); text-align: center; font: 500 .7rem/1 var(--ui); letter-spacing: .14em; text-transform: uppercase; padding: 11px 16px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.strip b { color: #f0a493; font-weight: 600; }
.mast { display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; gap: 16px; padding: 30px 0 10px; }
.mast .r { text-align: right; }
.mast .r a { text-decoration: none; }
.logo { text-decoration: none; text-align: center; color: var(--ink); }
.logo b { display: block; font: italic 800 clamp(2.4rem, 7vw, 4.6rem)/1 var(--display); letter-spacing: -.035em; }
.logo b span { color: var(--red); }
.sections { display: flex; justify-content: center; flex-wrap: wrap; gap: 6px 30px; padding: 16px 0 18px; border-bottom: 2px solid var(--ink); }
.sections a { font: 500 .74rem var(--ui); letter-spacing: .16em; text-transform: uppercase; text-decoration: none; color: var(--ink); }
.sections a:hover { color: var(--red); }

/* generated cover art */
.art { display: block; width: 100%; aspect-ratio: 4 / 3; background: var(--paper-2); }
.art svg { display: block; width: 100%; height: 100%; }

/* cover story */
.cover { display: grid; grid-template-columns: 1.15fr 1fr; gap: clamp(28px, 5vw, 64px); align-items: center; padding: clamp(36px, 6vw, 72px) 0; border-bottom: 1px solid var(--rule); text-decoration: none; }
.cover h2 { font: italic 800 clamp(2.6rem, 6.2vw, 5rem)/1.02 var(--display); letter-spacing: -.03em; color: var(--ink); margin: 14px 0 22px; text-wrap: balance; }
.cover .dek { font: 400 1.3rem/1.5 var(--serif); color: var(--text); margin: 0 0 18px; max-width: 30em; }
.byline { font: 400 .95rem var(--ui); color: var(--muted); }
.more { display: inline-block; margin-top: 22px; font: 500 1rem var(--ui); color: var(--red); border-bottom: 1px solid var(--red); padding-bottom: 2px; }
.cover:hover .more { padding-right: 6px; }
.cover:hover h2 { text-decoration: underline; text-decoration-thickness: 2px; text-underline-offset: 8px; }

/* contents + dispatches */
.lower { display: grid; grid-template-columns: minmax(0, 1fr) 300px; gap: clamp(28px, 5vw, 64px); padding: 44px 0 0; }
.hd { display: flex; align-items: baseline; justify-content: space-between; border-bottom: 1px solid var(--ink); padding-bottom: 10px; margin-bottom: 26px; }
.hd h3 { font: italic 800 1.6rem/1 var(--display); color: var(--ink); margin: 0; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 40px 32px; }
.story { text-decoration: none; display: block; }
.story h4 { font: 800 1.65rem/1.12 var(--display); letter-spacing: -.015em; color: var(--ink); margin: 16px 0 10px; }
.story:hover h4 { color: var(--red); }
.story p { font: 400 1.08rem/1.55 var(--serif); color: var(--text); margin: 0 0 10px; }
.story p.kicker { font: 500 .7rem/1.4 var(--mono); color: var(--red); }
.story .art { transition: filter .2s; } .story:hover .art { filter: saturate(1.25) contrast(1.05); }
.disp { list-style: none; margin: 0; padding: 0; counter-reset: d; }
.disp li { padding: 0 0 22px; margin: 0 0 22px; border-bottom: 1px solid var(--rule); }
.disp li:last-child { border-bottom: 0; }
.disp h5 { font: 600 1.15rem/1.3 var(--display); color: var(--ink); margin: 8px 0 6px; }
.disp p { font: 400 1rem/1.55 var(--serif); color: var(--text); margin: 0; }
.disp code, article :not(pre) > code { font: .84em var(--mono); background: var(--paper-2); padding: 1px 5px; border-radius: 3px; }
.quote { margin: 56px 0 0; padding: 40px 0; border-block: 2px solid var(--ink); text-align: center; }
.quote p { font: italic 600 clamp(1.6rem, 3.6vw, 2.4rem)/1.25 var(--display); color: var(--ink); max-width: 26em; margin: 0 auto; }
.quote .small { margin-top: 14px; display: block; }

/* article */
.progress { position: fixed; inset: 0 0 auto 0; height: 3px; background: var(--red); transform-origin: 0 50%; transform: scaleX(0); z-index: 20; }
.a-head { max-width: 900px; margin: 0 auto; text-align: center; padding: clamp(40px, 7vw, 84px) 0 34px; }
.a-head h1 { font: italic 800 clamp(2.6rem, 7vw, 5rem)/1.02 var(--display); letter-spacing: -.03em; color: var(--ink); margin: 18px 0 22px; text-wrap: balance; }
.a-head .dek { font: 400 clamp(1.15rem, 2.2vw, 1.4rem)/1.5 var(--serif); color: var(--text); max-width: 34em; margin: 0 auto; }
.a-meta { display: flex; justify-content: center; flex-wrap: wrap; align-items: center; gap: 8px 22px; margin-top: 26px; font: 400 .9rem var(--ui); color: var(--muted); }
.btn { font: 500 .78rem var(--ui); letter-spacing: .1em; text-transform: uppercase; color: var(--paper); background: var(--ink); border: 0; padding: 10px 16px; cursor: pointer; display: inline-flex; gap: 10px; align-items: center; }
.btn kbd { font: 500 .7rem var(--mono); opacity: .7; border: 1px solid currentColor; padding: 0 4px; border-radius: 2px; }
.hero-art { max-width: 1000px; margin: 0 auto 8px; }
.hero-art .art { aspect-ratio: 21 / 9; }
.caption { max-width: 1000px; margin: 0 auto; font: italic 400 .9rem var(--serif); color: var(--muted); padding-top: 6px; }
article { max-width: var(--measure); margin: 48px auto 0; font: 400 var(--size)/1.72 var(--read); color: var(--text); }
article > p:first-of-type::first-letter { float: left; font: 800 4.6em/.82 var(--display); color: var(--red); padding: .06em .1em 0 0; }
article p { margin: 0 0 1.25em; }
article h2 { font: italic 800 1.65em/1.15 var(--display); color: var(--ink); margin: 1.9em 0 .55em; letter-spacing: -.01em; }
article h3 { font: 600 1.05em/1.3 var(--ui); letter-spacing: .02em; color: var(--ink); margin: 1.7em 0 .4em; }
article .anchor { display: none; }
article ul, article ol { padding-left: 1.2em; margin: 0 0 1.25em; }
article li { margin: .4em 0; }
article li::marker { color: var(--red); }
article a { color: var(--red); text-underline-offset: 3px; text-decoration-thickness: 1px; }
article strong { color: var(--ink); font-weight: 600; }
article img { max-width: 100%; }
.callout { margin: 2em -2em; padding: 1.1em 2em; border-block: 2px solid var(--ink); text-align: center; }
.callout p { margin: 0; font: italic 600 1.3em/1.4 var(--display); color: var(--ink); }
.callout strong { display: block; font: 500 .52em/1 var(--mono); letter-spacing: .16em; text-transform: uppercase; color: var(--red); margin-bottom: 12px; }
.code { position: relative; margin: 1.6em 0; background: var(--ink); color: #efe8dc; border-radius: 2px; }
.code pre { margin: 0; overflow-x: auto; padding: 22px 22px 18px; font: 400 .74em/1.65 var(--mono); }
.code .lang { position: absolute; left: 22px; top: 6px; font: 500 .56em var(--mono); letter-spacing: .14em; text-transform: uppercase; color: #f0a493; }
.code .copy { position: absolute; right: 8px; top: 8px; font: 500 .6em var(--mono); color: #efe8dc; background: transparent; border: 1px solid #5a534a; padding: 3px 8px; cursor: pointer; }
.end { text-align: center; color: var(--red); font-size: 1.4rem; margin: 1.4em 0 0; }
.next { max-width: 1000px; margin: 64px auto 0; border-top: 2px solid var(--ink); padding-top: 22px; }
.next .grid { grid-template-columns: repeat(2, 1fr); }

.arow { display: grid; grid-template-columns: 150px 1fr auto; gap: 18px; padding: 16px 0; border-bottom: 1px solid var(--rule); }
@media (max-width: 600px) { .arow { grid-template-columns: 1fr; gap: 4px; } }
footer { margin-top: 96px; border-top: 2px solid var(--ink); padding: 26px 0 50px; display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; gap: 12px; font: 400 .85rem var(--ui); color: var(--muted); }
footer .logo b { font-size: 1.6rem; }
footer .r { text-align: right; }
footer a { color: var(--muted); }

/* reading mode */
.rbar { display: none; }
html.reading .strip, html.reading .mast, html.reading .sections, html.reading footer, html.reading .next, html.reading .hero-art, html.reading .caption, html.reading .btn-read { display: none; }
html.reading .a-head { padding-top: 96px; }
html.reading .rbar { display: flex; position: fixed; top: 14px; left: 50%; transform: translateX(-50%); z-index: 30; gap: 2px; align-items: center; padding: 5px; background: var(--ink); color: var(--paper); box-shadow: 0 10px 30px -12px rgba(0,0,0,.45); transition: opacity .3s; }
html.reading.idle .rbar { opacity: 0; }
html.reading.idle .rbar:hover, html.reading .rbar:focus-within { opacity: 1; }
.rbar button { font: 500 .74rem var(--ui); letter-spacing: .06em; color: inherit; background: none; border: 0; padding: 8px 10px; cursor: pointer; min-width: 32px; }
.rbar button:hover { background: rgba(255,255,255,.1); }
.rbar button[aria-pressed="true"] { color: #f0a493; }
.rbar .sep { width: 1px; height: 18px; background: rgba(255,255,255,.2); margin: 0 4px; }
.rbar .sw { width: 14px; height: 14px; border-radius: 50%; display: inline-block; vertical-align: -2px; border: 1px solid rgba(255,255,255,.4); }

@media (max-width: 900px) {
  .cover, .lower { grid-template-columns: 1fr; }
  .mast { grid-template-columns: 1fr; text-align: center; padding-top: 22px; } .mast .l, .mast .r { display: none; }
  .callout { margin-inline: 0; padding-inline: 0; }
}
@media (max-width: 600px) {
  :root { --size: 19px; }
  .grid, .next .grid { grid-template-columns: 1fr; }
  .sections { gap: 8px 18px; } .sections a { font-size: .68rem; }
  footer { grid-template-columns: 1fr; text-align: center; } footer .r { text-align: center; }
  html.reading .rbar { top: auto; bottom: 14px; } html.reading .a-head { padding-top: 36px; }
  .rbar .hide-sm { display: none; }
}
@media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
"""

BOOT = """<script>try{var s=JSON.parse(localStorage.getItem('nook-reader')||'{}'),d=document.documentElement;if(s.theme)d.dataset.theme=s.theme;if(s.font)d.dataset.font=s.font;if(s.size)d.style.setProperty('--size',s.size+'px');if(s.on&&location.pathname.indexOf('/p/')===0)d.classList.add('reading')}catch(e){}</script>"""

POST_JS = r"""<script>
(() => {
  const d = document.documentElement, KEY = 'nook-reader';
  let s; try { s = JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) { s = {}; }
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(s)); } catch (e) {} };
  const base = () => parseFloat(getComputedStyle(d).getPropertyValue('--size')) || 21;
  const sync = () => {
    document.querySelectorAll('[data-theme-set]').forEach(b => b.setAttribute('aria-pressed', (d.dataset.theme || 'paper') === b.dataset.themeSet));
    document.querySelectorAll('[data-font-set]').forEach(b => b.setAttribute('aria-pressed', (d.dataset.font || 'serif') === b.dataset.fontSet));
  };
  let t; const idle = () => { d.classList.remove('idle'); clearTimeout(t); t = setTimeout(() => d.classList.contains('reading') && d.classList.add('idle'), 2200); };
  const toggle = on => { on = on ?? !d.classList.contains('reading'); d.classList.toggle('reading', on); s.on = on; save(); sync(); if (on) { idle(); scrollTo({ top: 0 }); } };
  document.querySelectorAll('[data-read]').forEach(b => b.addEventListener('click', () => toggle()));
  document.querySelectorAll('[data-theme-set]').forEach(b => b.addEventListener('click', () => { const v = b.dataset.themeSet; if (v === 'paper') delete d.dataset.theme; else d.dataset.theme = v; s.theme = v === 'paper' ? '' : v; save(); sync(); }));
  document.querySelectorAll('[data-font-set]').forEach(b => b.addEventListener('click', () => { const v = b.dataset.fontSet; if (v === 'serif') delete d.dataset.font; else d.dataset.font = v; s.font = v === 'serif' ? '' : v; save(); sync(); }));
  document.querySelectorAll('[data-size]').forEach(b => b.addEventListener('click', () => { const n = Math.min(28, Math.max(15, base() + +b.dataset.size)); d.style.setProperty('--size', n + 'px'); s.size = n; save(); }));
  addEventListener('keydown', e => {
    if (e.metaKey || e.ctrlKey || e.altKey || /input|textarea/i.test(e.target.tagName)) return;
    const on = d.classList.contains('reading');
    if (e.key === 'r') toggle(); else if (e.key === 'Escape' && on) toggle(false);
    else if (on && (e.key === '+' || e.key === '=')) document.querySelector('[data-size="1"]').click();
    else if (on && e.key === '-') document.querySelector('[data-size="-1"]').click();
  });
  ['mousemove', 'touchstart', 'keydown'].forEach(ev => addEventListener(ev, idle, { passive: true }));
  const bar = document.querySelector('.progress'), art = document.querySelector('article');
  const tick = () => { const r = art.getBoundingClientRect(); bar.style.transform = `scaleX(${Math.min(1, Math.max(0, -r.top / Math.max(r.height - innerHeight * .6, 1)))})`; };
  addEventListener('scroll', tick, { passive: true }); tick();
  document.querySelectorAll('.code .copy').forEach(b => b.addEventListener('click', async () => {
    try { await navigator.clipboard.writeText(b.parentElement.querySelector('code').innerText); b.textContent = 'copied'; } catch (e) { b.textContent = 'press ⌘C'; }
    setTimeout(() => b.textContent = 'copy', 1400); }));
  sync(); if (d.classList.contains('reading')) idle();
})();
</script>"""

# Each story gets its own abstract cover, drawn from its slug, so the page has pictures without stock photos.
PALETTES = [("#e9dcc6", "#a3261b", "#1d3b53", "#e2a33b"), ("#dfe6dc", "#2f5d50", "#c9532f", "#121110"), ("#efd9cf", "#7b2d43", "#f0a493", "#2b2723"),
            ("#dde3ea", "#24435f", "#e2a33b", "#a3261b"), ("#ece4cf", "#5b6b2f", "#121110", "#c9532f"), ("#e8dfee", "#4b2e6b", "#e2a33b", "#1d3b53")]
def art(slug, label=""):
    h = 0
    for ch in slug: h = (h * 131 + ord(ch)) % 2**31
    rnd = lambda n: (h >> n) % 1000 / 1000
    bg, a, b, c = PALETTES[h % len(PALETTES)]
    kind = (h >> 3) % 4
    s = [f'<rect width="400" height="300" fill="{bg}"/>']
    if kind == 0:   # sun over waves
        s.append(f'<circle cx="{120 + rnd(5) * 160:.0f}" cy="{110 + rnd(7) * 30:.0f}" r="{60 + rnd(9) * 30:.0f}" fill="{a}"/>')
        for i in range(6):
            y = 170 + i * 22
            s.append(f'<path d="M0 {y} Q 50 {y - 14} 100 {y} T 200 {y} T 300 {y} T 400 {y} V300 H0Z" fill="{b if i % 2 else c}" opacity="{.55 + i * .07:.2f}"/>')
    elif kind == 1:  # stacked bars, like a waveform
        n = 18
        for i in range(n):
            v = ((h >> (i % 24)) % 100) / 100
            hgt = 40 + v * 170
            s.append(f'<rect x="{22 + i * 20}" y="{150 - hgt / 2:.0f}" width="11" height="{hgt:.0f}" rx="5.5" fill="{a if i % 5 else c}"/>')
        s.append(f'<rect x="0" y="262" width="400" height="38" fill="{b}"/>')
    elif kind == 2:  # arcs
        for i in range(7):
            r = 250 - i * 34
            s.append(f'<circle cx="{40 + rnd(4) * 60:.0f}" cy="300" r="{r}" fill="{[a, b, c][i % 3]}"/>')
        s.append(f'<circle cx="{300 + rnd(6) * 50:.0f}" cy="{70 + rnd(8) * 40:.0f}" r="22" fill="{c}"/>')
    else:            # grid of dots with one highlighted path
        for x in range(10):
            for y in range(7):
                hit = (x * 7 + y + h) % 11 == 0
                s.append(f'<circle cx="{38 + x * 36}" cy="{42 + y * 36}" r="{9 if hit else 4}" fill="{a if hit else b}"/>')
        s.append(f'<path d="M38 222 L {110 + rnd(3) * 60:.0f} 150 L {220 + rnd(5) * 40:.0f} 186 L 362 78" fill="none" stroke="{c}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>')
    return f'<span class="art" role="img" aria-label="{html.escape(label)}"><svg viewBox="0 0 400 300" preserveAspectRatio="xMidYMid slice">{"".join(s)}</svg></span>'

SECTIONS = [("Features", "/#contents"), ("Dispatches", "/#dispatches"), ("Engineering", "/#contents"), ("Archive", "/archive"), ("About", "/about")]

def page(title, desc, path, body, script="", strip=True):
    t, dsc = html.escape(title), html.escape(desc)
    issue = f'Issue No. {len(posts)} · <b>{html.escape(posts[0]["title"])}</b> · notes from building in public' if posts else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{t}</title>
<meta name="description" content="{dsc}">
<meta property="og:title" content="{t}"><meta property="og:description" content="{dsc}"><meta property="og:site_name" content="{NAME}">
<meta name="twitter:card" content="summary">
<meta name="theme-color" content="#f4ede1">
<link rel="canonical" href="{SITE}{path}">
<link rel="alternate" type="application/rss+xml" title="{NAME}" href="/feed.xml">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
{BOOT}
{FONTS}
<style>{CSS}</style>
</head>
<body>
<div class="strip">{issue}</div>
<div class="wrap">
<header class="mast">
  <span class="small l">Vol. I · {date.today().strftime("%B %Y")}</span>
  <a class="logo" href="/" aria-label="{NAME}, home"><b>The Digital Nook<span>.</span></b></a>
  <span class="small r"></span>
</header>
<nav class="sections" aria-label="Sections">{"".join(f'<a href="{u}">{n}</a>' for n, u in SECTIONS)}</nav>
{body}
<footer><span>© {date.today().year} {NAME}</span><a class="logo" href="/"><b>The Digital Nook<span>.</span></b></a><span class="r">Plain HTML · no trackers · <a href="/feed.xml">RSS</a></span></footer>
</div>
{script}
</body>
</html>
"""

# ---------- Build ----------
iso = lambda d: d.isoformat()
nice = lambda d: d.strftime("%B %-d, %Y")
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
notes = [p for p in posts if p["note"]]
section = lambda p: (p["tags"][0] if p["tags"] else "feature").title()

if os.path.isdir(OUT):
    for x in os.listdir(OUT):
        if x != ".vercel": shutil.rmtree(os.path.join(OUT, x)) if os.path.isdir(os.path.join(OUT, x)) else os.remove(os.path.join(OUT, x))
os.makedirs(os.path.join(OUT, "p"), exist_ok=True)

READBAR = """<div class="rbar" role="toolbar" aria-label="Reading settings">
  <button type="button" data-size="-1" aria-label="Smaller text">A−</button><button type="button" data-size="1" aria-label="Larger text">A+</button>
  <span class="sep"></span>
  <button type="button" data-font-set="serif">Serif</button><button type="button" data-font-set="sans">Sans</button>
  <span class="sep"></span>
  <button type="button" data-theme-set="paper" aria-label="Paper"><span class="sw" style="background:#f4ede1"></span></button><button type="button" data-theme-set="white" aria-label="White"><span class="sw" style="background:#fdfcfa"></span></button><button type="button" data-theme-set="dark" aria-label="Dark"><span class="sw" style="background:#16140f"></span></button>
  <span class="sep"></span>
  <button type="button" data-read aria-label="Leave reading mode">✕<span class="hide-sm">&nbsp;Exit</span></button>
</div>"""

def story(p):
    return f'<a class="story" href="/p/{p["slug"]}">{art(p["slug"])}<p class="kicker" style="margin:16px 0 0">{section(p)} · {p["mins"]} min</p><h4>{html.escape(p["title"])}</h4><p>{html.escape(p["summary"])}</p><span class="byline">{nice(p["date"])}</span></a>'

for i, p in enumerate(essays):
    others = [q for q in essays if q is not p][:2]
    body = f"""<div class="progress" aria-hidden="true"></div>
{READBAR}
<main>
  <header class="a-head">
    <p class="kicker">{section(p)} · {p["words"]:,} words</p>
    <h1>{html.escape(p["title"])}</h1>
    {f'<p class="dek">{html.escape(p["summary"])}</p>' if p["summary"] else ""}
    <div class="a-meta"><span>From the Nook</span><span>{nice(p["date"])}</span><span>{p["mins"]} min read</span>
      <button class="btn btn-read" type="button" data-read>Reading mode <kbd>R</kbd></button></div>
  </header>
  <figure class="hero-art" style="margin:0 auto">{art(p["slug"], "Abstract cover illustration")}</figure>
  <p class="caption">Cover: generated for this story.</p>
  <article>
{p["body"]}
    <p class="end" aria-hidden="true">■</p>
  </article>
  {f'<section class="next"><div class="hd"><h3>Keep reading</h3><a class="small" href="/archive">Archive →</a></div><div class="grid">{"".join(story(q) for q in others)}</div></section>' if others else ""}
</main>"""
    open(os.path.join(OUT, "p", p["slug"] + ".html"), "w").write(page(f'{p["title"]} — {NAME}', p["summary"], f'/p/{p["slug"]}', body, POST_JS))

lead = essays[0] if essays else None
cover = f"""<a class="cover" href="/p/{lead["slug"]}">
    {art(lead["slug"], "Cover illustration")}
    <div>
      <p class="kicker">Cover story · {lead["words"]:,} words</p>
      <h2>{html.escape(lead["title"])}</h2>
      <p class="dek">{html.escape(lead["summary"])}</p>
      <span class="byline">From the Nook · {nice(lead["date"])} · {lead["mins"]} min read</span><br>
      <span class="more">Read the story →</span>
    </div>
  </a>""" if lead else ""
disp = "".join(f'<li id="{n["slug"]}"><span class="kicker">{n["date"].strftime("%b %-d")}</span><h5>{html.escape(n["title"])}</h5>{n["body"]}</li>' for n in notes)
home = f"""<main>
  {cover}
  <div class="lower">
    <section id="contents"><div class="hd"><h3>In this issue</h3><span class="small">{len(essays)} stories</span></div>
      <div class="grid">{"".join(story(p) for p in essays[1:])}</div></section>
    <aside id="dispatches"><div class="hd"><h3>Dispatches</h3><span class="small">short notes</span></div><ul class="disp">{disp}</ul></aside>
  </div>
  <section class="quote"><p>“Most products show the finished thing. This is the part in between.”</p><span class="small">— The Nook, on why it exists</span></section>
</main>"""
open(os.path.join(OUT, "index.html"), "w").write(page(NAME, TAGLINE, "/", home))

rows = "".join(f'<li class="arow"><span class="small">{nice(p["date"])}</span><a href="{"/p/" + p["slug"] if not p["note"] else "/#" + p["slug"]}" style="font:700 1.25rem/1.3 var(--display);color:var(--ink);text-decoration:none">{html.escape(p["title"])}</a><span class="kicker">{"Dispatch" if p["note"] else section(p)}</span></li>' for p in posts)
archive = f'<main><header class="a-head"><p class="kicker">Archive</p><h1>Everything, in order.</h1></header><ul style="list-style:none;padding:0;max-width:900px;margin:0 auto">{rows}</ul></main>'
open(os.path.join(OUT, "archive.html"), "w").write(page(f"Archive — {NAME}", "Every story and dispatch.", "/archive", archive))

about = f"""<main>
  <header class="a-head"><p class="kicker">About</p><h1>A small corner for the work behind the work.</h1>
  <p class="dek">Stories, dispatches and measurements from building software in public.</p></header>
  <article>
<p>{NAME} is where the in-between parts get written down: the bugs that took too long to find, the numbers behind each decision, and the questions still open.</p>
<p>Right now most of it is about <a href="https://freshflo.vercel.app">Freshflo</a>, a dictation app for Mac, Windows and Android, on its way to launch.</p>
<h2 id="read">Made for reading</h2>
<p>Every story has a <strong>reading mode</strong>. Press <code>R</code> and everything but the words disappears; choose the text size, serif or sans, and a paper, white or dark page. It remembers your choice.</p>
<p>The site is plain HTML built from Markdown files by one small script. No trackers, no cookies. Follow along by <a href="/feed.xml">RSS</a>.</p>
  </article>
</main>"""
open(os.path.join(OUT, "about.html"), "w").write(page(f"About — {NAME}", "What The Digital Nook is and how it's made.", "/about", about))
open(os.path.join(OUT, "404.html"), "w").write(page(f"Not found — {NAME}", "Page not found.", "/404", '<main><header class="a-head"><p class="kicker">404</p><h1>This page wandered off.</h1><p class="dek"><a href="/">Back to the current issue →</a></p></header></main>'))
open(os.path.join(OUT, "favicon.svg"), "w").write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="6" fill="#121110"/><text x="16" y="23" text-anchor="middle" font-family="Georgia,serif" font-style="italic" font-weight="800" font-size="20" fill="#f4ede1">N</text><circle cx="24.5" cy="21.5" r="2.2" fill="#a3261b"/></svg>')

rfc = lambda d: format_datetime(datetime(d.year, d.month, d.day, tzinfo=timezone.utc))
link = lambda p: f"{SITE}/#{p['slug']}" if p["note"] else f"{SITE}/p/{p['slug']}"
items = "\n".join(f"  <item><title>{html.escape(p['title'])}</title><link>{link(p)}</link><guid>{link(p)}</guid><pubDate>{rfc(p['date'])}</pubDate><description>{html.escape(p['summary'] or re.sub(r'<[^>]+>', '', p['body']))}</description></item>" for p in posts)
open(os.path.join(OUT, "feed.xml"), "w").write(f'<?xml version="1.0" encoding="utf-8"?>\n<rss version="2.0"><channel>\n  <title>{NAME}</title><link>{SITE}</link><description>{html.escape(TAGLINE)}</description>\n{items}\n</channel></rss>\n')
open(os.path.join(OUT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
urls = ["/", "/about", "/archive"] + [f"/p/{p['slug']}" for p in essays]
open(os.path.join(OUT, "sitemap.xml"), "w").write('<?xml version="1.0" encoding="utf-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(f"  <url><loc>{SITE}{u}</loc></url>" for u in urls) + "\n</urlset>\n")
shutil.copy(os.path.join(ROOT, "vercel.json"), os.path.join(OUT, "vercel.json"))
print(f"✓ {NAME}: {len(essays)} stories, {len(notes)} dispatches → dist/")
