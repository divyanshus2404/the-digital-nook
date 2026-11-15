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
TAGLINE = "The story of building Freshflo, a dictation app made in the open: every bug, measurement and decision on the way to launch."
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

# ---------- Look: Freshflo's own brand (pearl, ink, mint), told as a story ----------
import json
STORY = json.load(open(os.path.join(ROOT, "content", "_story.json")))
APP = "https://freshflo.vercel.app"
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Bricolage+Grotesque:opsz,wdth,wght@12..96,75..100,600..800&family=Hanken+Grotesk:ital,wght@0,400..700;1,400&family=Newsreader:ital,opsz,wght@0,6..72,400;1,6..72,400&family=JetBrains+Mono:wght@400;500&display=swap">')

# The Freshflo mark: a messy voice line that settles into one clean stroke and a full stop.
MARK_PATH = "M210 512 L248 404 L290 616 L332 446 L370 564 L400 498 C 424 444, 476 404, 514 458 C 550 506, 562 588, 612 588 C 654 588, 670 512, 714 512"
def mark(cls="", w=None):
    return (f'<svg class="mark {cls}" viewBox="180 360 650 300" aria-hidden="true"{f" width={w}" if w else ""}>'
            '<defs><linearGradient id="mk" x1="210" y1="0" x2="714" y2="0" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#b3c2be"/><stop offset=".3" stop-color="#7d9c95"/><stop offset=".55" stop-color="#17a884"/><stop offset="1" stop-color="#22c99b"/></linearGradient></defs>'
            f'<path class="line" d="{MARK_PATH}" fill="none" stroke="url(#mk)" stroke-width="40" stroke-linecap="round" stroke-linejoin="round" pathLength="1"/>'
            '<circle class="dot" cx="786" cy="512" r="31" fill="#0e9f79"/></svg>')

CSS = r"""
:root {
  --bg: #f8fbfa; --surface: #ffffff; --sunk: #eef4f2; --ink: #0c2421; --text: #20332f; --muted: #4b625e; --faint: #6f8480; --line: #dde7e3;
  --fresh: #0e9f79; --fresh-ink: #087a5c; --mint: #e9f8f1; --cta: #bdf0db;
  --serif: "Instrument Serif", Georgia, serif; --body: "Hanken Grotesk", system-ui, -apple-system, sans-serif; --display: "Bricolage Grotesque", system-ui, sans-serif;
  --book: "Newsreader", Georgia, serif; --mono: "JetBrains Mono", ui-monospace, Menlo, monospace;
  --read: var(--body); --size: 20px; --measure: 66ch; --shadow: 0 1px 0 rgba(12,36,33,.04), 0 22px 44px -28px rgba(12,36,33,.35); color-scheme: light;
}
html[data-theme="sepia"] { --bg: #f6f0e4; --surface: #fbf6ec; --sunk: #efe6d4; --ink: #2b2216; --text: #3b3022; --muted: #6f604b; --faint: #8a7a63; --line: #e4d9c4; --mint: #efe6d4; }
html[data-theme="dark"] { --bg: #0b1311; --surface: #131d1b; --sunk: #0f1816; --ink: #e8f2ef; --text: #c9d8d4; --muted: #a3b6b1; --faint: #8aa09a; --line: #24332f; --fresh: #3ddbab; --fresh-ink: #62e7bf; --mint: #0e1f1a; --cta: #3ddbab; color-scheme: dark; }
html[data-font="serif"] { --read: var(--book); }
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; scroll-padding-top: 90px; scroll-behavior: smooth; }
body { margin: 0; background: var(--bg); color: var(--text); font: 400 17px/1.65 var(--body); -webkit-font-smoothing: antialiased; }
a { color: inherit; }
::selection { background: var(--cta); color: #0c2421; }
:focus-visible { outline: 2px solid var(--fresh); outline-offset: 3px; border-radius: 6px; }
.wrap { max-width: 1160px; margin: 0 auto; padding: 0 clamp(18px, 4vw, 44px); }
.eyebrow { font: 500 .74rem/1.4 var(--mono); letter-spacing: .14em; text-transform: uppercase; color: var(--faint); margin: 0; }
.eyebrow b { color: var(--fresh-ink); font-weight: 500; }
h1, h2, h3 { color: var(--ink); }
em { color: var(--fresh-ink); }

/* header */
.top { position: sticky; top: 12px; z-index: 10; margin: 12px auto 0; max-width: 1160px; padding: 0 clamp(10px, 3vw, 32px); }
.top .in { display: flex; align-items: center; justify-content: space-between; gap: 14px; padding: 9px 10px 9px 14px; border: 1px solid var(--line); border-radius: 999px; background: color-mix(in srgb, var(--surface) 82%, transparent); backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px); box-shadow: var(--shadow); }
.brand { display: inline-flex; align-items: center; gap: 10px; text-decoration: none; color: var(--ink); }
.brand img { width: 32px; height: 32px; }
.brand b { font: 680 1.2rem/1 var(--display); letter-spacing: -.035em; font-variation-settings: "wdth" 88; }
.brand b i { font-style: normal; color: var(--fresh); }
.brand span { font: 400 1.15rem/1 var(--serif); font-style: italic; color: var(--muted); padding-left: 10px; border-left: 1px solid var(--line); }
.top nav { display: flex; align-items: center; gap: 22px; font-size: .92rem; }
.top nav a { text-decoration: none; color: var(--muted); }
.top nav a:hover { color: var(--ink); }
.pill { display: inline-flex; align-items: center; gap: 8px; font: 600 .9rem var(--body); text-decoration: none; color: #0c2421 !important; background: var(--cta); border: 1px solid #0c2421; border-radius: 999px; padding: 9px 16px; box-shadow: 0 2px 0 #0c2421; transition: transform .15s, box-shadow .15s; }
.pill:hover { transform: translateY(-1px); box-shadow: 0 3px 0 #0c2421; }
.pill.ghost { background: transparent; color: var(--ink) !important; border-color: var(--line); box-shadow: none; }

/* hero */
.hero { display: grid; grid-template-columns: 1.1fr .9fr; gap: clamp(28px, 5vw, 64px); align-items: center; padding: clamp(48px, 9vw, 110px) 0 clamp(36px, 6vw, 64px); }
.hero h1 { font: 400 clamp(3rem, 7.4vw, 5.6rem)/.98 var(--serif); letter-spacing: -.025em; margin: 18px 0 22px; text-wrap: balance; }
.hero .lede { font-size: 1.2rem; color: var(--muted); max-width: 32em; margin: 0 0 30px; }
.hero .actions { display: flex; flex-wrap: wrap; gap: 12px; }
.tile { position: relative; aspect-ratio: 1; border-radius: 22%; background: linear-gradient(#fff, #f4f9f7 55%, #e2efea); border: 1px solid var(--line); box-shadow: 0 40px 80px -40px rgba(12,36,33,.45), inset 0 0 0 3px #fff; display: grid; place-items: center; max-width: 440px; justify-self: center; width: 100%; }
html[data-theme="dark"] .tile { background: linear-gradient(#18241f, #111a17); box-shadow: 0 40px 80px -40px #000; }
.tile .mark { width: 76%; filter: drop-shadow(0 14px 14px rgba(14,159,121,.22)); }
.tile { align-content: center; gap: 0; padding: 9% 8%; }
.tile .mark { width: 62%; height: auto; aspect-ratio: 650 / 300; justify-self: center; margin-bottom: 6%; }
.demo { width: 100%; display: grid; gap: 10px; }
.demo p { margin: 0; display: flex; gap: 10px; align-items: flex-start; padding: 11px 14px; border-radius: 14px; font-size: .9rem; line-height: 1.4; min-height: 3.2em; }
.demo .said { background: var(--sunk); color: var(--faint); font-style: italic; }
.demo .sent { background: var(--surface); color: var(--ink); font-weight: 600; border: 1px solid var(--line); box-shadow: 0 10px 22px -16px rgba(14,159,121,.5); opacity: 0; transform: translateY(6px); transition: opacity .5s, transform .5s; }
.demo.done .sent { opacity: 1; transform: none; }
.demo .rec { flex: none; width: 9px; height: 9px; margin-top: 5px; border-radius: 50%; background: #e5484d; animation: blink 1s infinite; }
.demo.done .rec { animation: none; background: var(--faint); }
.demo .ok { flex: none; color: var(--fresh); }
@keyframes blink { 50% { opacity: .25; } }
.tile figcaption { position: absolute; bottom: 4.5%; font: 400 1.15rem var(--serif); font-style: italic; color: var(--muted); }
.mark .line { stroke-dasharray: 1; stroke-dashoffset: 1; animation: draw 2.4s cubic-bezier(.6,.05,.25,1) .3s forwards; }
.mark .dot { transform-origin: 786px 512px; transform: scale(0); animation: pop .5s cubic-bezier(.3,1.6,.5,1) 2.5s forwards; }
@keyframes draw { to { stroke-dashoffset: 0; } }
@keyframes pop { to { transform: scale(1); } }

/* stats */
.stats { display: grid; grid-template-columns: repeat(4, 1fr); border: 1px solid var(--line); border-radius: 22px; background: var(--surface); box-shadow: var(--shadow); overflow: hidden; }
.stats > div { padding: 22px 24px; border-left: 1px solid var(--line); }
.stats > div:first-child { border-left: 0; }
.stats b { display: block; font: 400 2.6rem/1 var(--serif); color: var(--ink); }
.stats span { font-size: .9rem; color: var(--muted); }
.stats .bar { height: 6px; border-radius: 6px; background: var(--sunk); margin: 10px 0 6px; overflow: hidden; }
.stats .bar i { display: block; height: 100%; background: var(--fresh); border-radius: 6px; }

/* section heads */
.sec { padding: clamp(64px, 9vw, 112px) 0 0; }
.sec-head { display: flex; align-items: end; justify-content: space-between; gap: 20px; margin-bottom: 34px; }
.sec-head h2 { font: 400 clamp(2.2rem, 4.6vw, 3.4rem)/1.02 var(--serif); letter-spacing: -.02em; margin: 10px 0 0; }
.sec-head p { color: var(--muted); max-width: 26em; margin: 0; }

/* the story: chapters along the brand line */
.chapters { position: relative; list-style: none; margin: 0; padding: 0 0 0 54px; }
.chapters::before { content: ""; position: absolute; left: 17px; top: 10px; bottom: 10px; width: 3px; border-radius: 3px; background: linear-gradient(#b3c2be, #7d9c95 35%, #17a884 70%, #22c99b); }
.chapters > li { position: relative; padding: 0 0 38px; }
.chapters > li::before { content: attr(data-n); position: absolute; left: -54px; top: -2px; width: 37px; height: 37px; border-radius: 50%; background: var(--surface); border: 2px solid var(--fresh); display: grid; place-items: center; font: 500 .74rem var(--mono); color: var(--fresh-ink); }
.chapters time { font: 500 .74rem var(--mono); letter-spacing: .1em; text-transform: uppercase; color: var(--faint); }
.chapters h3 { font: 400 1.9rem/1.1 var(--serif); margin: 4px 0 6px; }
.chapters p { margin: 0; color: var(--muted); max-width: 40em; }
.chapters a.read { display: inline-block; margin-top: 10px; font-weight: 600; font-size: .95rem; color: var(--fresh-ink); text-decoration: none; }
.chapters a.read:hover { text-decoration: underline; text-underline-offset: 3px; }
.chapters li.next::before { content: "→"; background: var(--fresh); color: #fff; border-color: var(--fresh); }
.chapters li.next h3 em { color: var(--fresh-ink); }
.left { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }
.left span { font-size: .88rem; padding: 6px 12px; border-radius: 999px; border: 1px solid var(--line); background: var(--surface); color: var(--text); }
.left span.doing { border-color: var(--fresh); background: var(--mint); }
.left span.doing::after { content: " · now"; color: var(--fresh-ink); font-weight: 600; }

/* stories */
.stories { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; }
.card { display: flex; flex-direction: column; text-decoration: none; background: var(--surface); border: 1px solid var(--line); border-radius: 24px; overflow: hidden; box-shadow: var(--shadow); transition: transform .2s, box-shadow .2s; }
.card:hover { transform: translateY(-4px); box-shadow: 0 30px 60px -30px rgba(12,36,33,.4); }
.card .body { padding: 20px 22px 24px; display: flex; flex-direction: column; gap: 8px; flex: 1; }
.card h3 { font: 400 1.75rem/1.1 var(--serif); margin: 0; }
.card p { margin: 0; color: var(--muted); font-size: .98rem; }
.card .foot { margin-top: auto; padding-top: 8px; font: 500 .74rem var(--mono); color: var(--faint); letter-spacing: .06em; text-transform: uppercase; }
.card.lead { grid-column: 1 / -1; flex-direction: row; }
.card.lead .art { width: 55%; aspect-ratio: auto; }
.card.lead .body { padding: 34px; justify-content: center; }
.card.lead h3 { font-size: clamp(2rem, 3.6vw, 2.9rem); }
.art { display: block; width: 100%; aspect-ratio: 16 / 10; background: var(--sunk); }
.art svg { display: block; width: 100%; height: 100%; }

/* dispatches */
.disp { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }
.disp article { background: var(--mint); border: 1px solid var(--line); border-radius: 20px; padding: 22px 24px; margin: 0; max-width: none; font: inherit; }
.disp h3 { font: 600 1.08rem/1.35 var(--body); margin: 6px 0 6px; }
.disp p { margin: 0; color: var(--text); font-size: .98rem; }
.disp p.eyebrow, .card p.eyebrow { font-size: .74rem; color: var(--faint); }
code { font: .86em var(--mono); background: var(--sunk); padding: 1px 6px; border-radius: 5px; }

/* call to action */
.cta { margin-top: clamp(72px, 10vw, 120px); border-radius: 32px; background: #0c2421; color: #e8f2ef; padding: clamp(36px, 6vw, 64px); display: grid; grid-template-columns: auto 1fr auto; gap: 32px; align-items: center; }
.cta img { width: 88px; height: 88px; }
.cta h2 { font: 400 clamp(2rem, 4vw, 3rem)/1.05 var(--serif); color: #fff; margin: 0 0 6px; }
.cta h2 em { color: #62e7bf; }
.cta p { margin: 0; color: #a3b6b1; }

footer { margin-top: 56px; padding: 26px 0 44px; border-top: 1px solid var(--line); display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 14px; font-size: .9rem; color: var(--muted); }
footer a { color: var(--muted); text-decoration: none; } footer a:hover { color: var(--ink); }
footer .brand img { width: 24px; height: 24px; } footer .brand b { font-size: 1rem; } footer .brand span { font-size: 1rem; }

/* article */
.progress { position: fixed; inset: 0 0 auto 0; height: 3px; background: var(--fresh); transform-origin: 0 50%; transform: scaleX(0); z-index: 40; }
.a-head { max-width: 860px; margin: 0 auto; text-align: center; padding: clamp(48px, 8vw, 96px) 0 34px; }
.a-head .chap { display: inline-flex; align-items: center; gap: 10px; }
.a-head .chap .mark { width: 54px; }
.a-head .chap .mark .line, .a-head .chap .mark .dot { animation: none; stroke-dashoffset: 0; transform: none; }
.a-head h1 { font: 400 clamp(2.8rem, 7vw, 5rem)/1 var(--serif); letter-spacing: -.025em; margin: 18px 0 20px; text-wrap: balance; }
.a-head .dek { font-size: clamp(1.1rem, 2.2vw, 1.3rem); color: var(--muted); max-width: 34em; margin: 0 auto; }
.a-meta { display: flex; justify-content: center; flex-wrap: wrap; align-items: center; gap: 8px 20px; margin-top: 26px; font-size: .92rem; color: var(--faint); }
.btn { font: 600 .88rem var(--body); color: var(--ink); background: var(--surface); border: 1px solid var(--line); border-radius: 999px; padding: 8px 14px; cursor: pointer; display: inline-flex; gap: 8px; align-items: center; }
.btn:hover { border-color: var(--fresh); }
.btn kbd { font: 500 .7rem var(--mono); color: var(--faint); border: 1px solid var(--line); padding: 0 5px; border-radius: 4px; }
.hero-art { max-width: 1040px; margin: 0 auto; border-radius: 28px; overflow: hidden; border: 1px solid var(--line); box-shadow: var(--shadow); }
.hero-art .art { aspect-ratio: 21 / 9; }
article.post { max-width: var(--measure); margin: 56px auto 0; font: 400 var(--size)/1.75 var(--read); color: var(--text); }
article.post > p:first-of-type::first-letter { float: left; font: 400 4.4em/.8 var(--serif); color: var(--fresh-ink); padding: .08em .12em 0 0; }
article.post p { margin: 0 0 1.25em; }
article.post h2 { font: 400 1.75em/1.12 var(--serif); margin: 1.8em 0 .5em; letter-spacing: -.01em; }
article.post h3 { font: 650 1.05em/1.35 var(--body); margin: 1.7em 0 .4em; }
article.post .anchor { display: none; }
article.post ul, article.post ol { padding-left: 1.25em; margin: 0 0 1.25em; }
article.post li { margin: .4em 0; }
article.post li::marker { color: var(--fresh); }
article.post a { color: var(--fresh-ink); text-underline-offset: 3px; }
article.post strong { color: var(--ink); font-weight: 650; }
article.post img { max-width: 100%; border-radius: 14px; }
.callout { margin: 2em 0; padding: 22px 26px; border-radius: 18px; background: var(--mint); border: 1px solid var(--line); }
.callout p { margin: 0; font: 400 1.25em/1.4 var(--serif); color: var(--ink); }
.callout strong { display: block; font: 500 .55em/1 var(--mono); letter-spacing: .14em; text-transform: uppercase; color: var(--fresh-ink); margin-bottom: 10px; }
.code { position: relative; margin: 1.6em 0; background: #0c2421; color: #e8f2ef; border-radius: 16px; }
.code pre code { background: none; padding: 0; border-radius: 0; font: inherit; color: inherit; }
.code pre { margin: 0; overflow-x: auto; padding: 24px 22px 18px; font: 400 .74em/1.65 var(--mono); }
.code .lang { position: absolute; left: 22px; top: 7px; font: 500 .56em var(--mono); letter-spacing: .14em; text-transform: uppercase; color: #62e7bf; }
.code .copy { position: absolute; right: 10px; top: 10px; font: 500 .6em var(--mono); color: #e8f2ef; background: transparent; border: 1px solid #2b4440; border-radius: 6px; padding: 3px 8px; cursor: pointer; }
.end { display: flex; justify-content: center; margin: 2.4em 0 0; }
.end .mark { width: 70px; } .end .mark .line, .end .mark .dot { animation: none; stroke-dashoffset: 0; transform: none; }
.chapnav { max-width: 1040px; margin: 72px auto 0; display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.chapnav a { display: block; text-decoration: none; padding: 22px 24px; border-radius: 22px; border: 1px solid var(--line); background: var(--surface); box-shadow: var(--shadow); }
.chapnav a:hover { border-color: var(--fresh); }
.chapnav a.n { text-align: right; }
.chapnav b { display: block; font: 400 1.6rem/1.15 var(--serif); color: var(--ink); margin-top: 6px; }

/* reading mode */
.rbar { display: none; }
html.reading .top, html.reading footer, html.reading .chapnav, html.reading .hero-art, html.reading .btn-read, html.reading .cta { display: none; }
html.reading .a-head { padding-top: 92px; }
html.reading .rbar { display: flex; position: fixed; top: 14px; left: 50%; transform: translateX(-50%); z-index: 30; gap: 2px; align-items: center; padding: 5px; border-radius: 999px; background: #0c2421; color: #e8f2ef; box-shadow: 0 14px 34px -14px rgba(0,0,0,.5); transition: opacity .3s; }
html.reading.idle .rbar { opacity: 0; }
html.reading.idle .rbar:hover, html.reading .rbar:focus-within { opacity: 1; }
.rbar button { font: 600 .8rem var(--body); color: inherit; background: none; border: 0; border-radius: 999px; padding: 8px 11px; cursor: pointer; min-width: 34px; }
.rbar button:hover { background: rgba(255,255,255,.1); }
.rbar button[aria-pressed="true"] { background: #bdf0db; color: #0c2421; }
.rbar .sep { width: 1px; height: 18px; background: rgba(255,255,255,.2); margin: 0 4px; }
.rbar .sw { width: 14px; height: 14px; border-radius: 50%; display: inline-block; vertical-align: -2px; border: 1px solid rgba(255,255,255,.5); }

@media (max-width: 960px) {
  .hero { grid-template-columns: 1fr; } .tile { max-width: 320px; }
  .stories { grid-template-columns: 1fr 1fr; }
  .cta { grid-template-columns: 1fr; text-align: left; }
  .top nav .hide-md { display: none; }
}
@media (max-width: 640px) {
  body { font-size: 16px; } :root { --size: 18.5px; }
  .brand span { display: none; }
  .top nav { gap: 14px; } .top nav .hide-sm { display: none; }
  .stats { grid-template-columns: 1fr 1fr; } .stats > div:nth-child(3) { border-left: 0; } .stats > div:nth-child(n+3) { border-top: 1px solid var(--line); }
  .stories, .disp, .chapnav { grid-template-columns: 1fr; } .card.lead { grid-column: auto; flex-direction: column; } .card.lead .art { width: 100%; aspect-ratio: 16/10; } .card.lead .body { padding: 22px; }
  .chapnav a.n { text-align: left; }
  .sec-head { flex-direction: column; align-items: start; }
  .hero-art { border-radius: 18px; }
  html.reading .rbar { top: auto; bottom: 14px; } html.reading .a-head { padding-top: 40px; }
  .rbar .hide-sm { display: none; }
}
@media (prefers-reduced-motion: reduce) { * { animation: none !important; transition: none !important; } .mark .line { stroke-dashoffset: 0; } .mark .dot { transform: none; } html { scroll-behavior: auto; } }
"""

BOOT = """<script>try{var s=JSON.parse(localStorage.getItem('nook-reader')||'{}'),d=document.documentElement;if(s.theme)d.dataset.theme=s.theme;if(s.font)d.dataset.font=s.font;if(s.size)d.style.setProperty('--size',s.size+'px');if(s.on&&location.pathname.indexOf('/p/')===0)d.classList.add('reading')}catch(e){}</script>"""

POST_JS = r"""<script>
(() => {
  const d = document.documentElement, KEY = 'nook-reader';
  let s; try { s = JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) { s = {}; }
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(s)); } catch (e) {} };
  const base = () => parseFloat(getComputedStyle(d).getPropertyValue('--size')) || 20;
  const sync = () => {
    document.querySelectorAll('[data-theme-set]').forEach(b => b.setAttribute('aria-pressed', (d.dataset.theme || 'light') === b.dataset.themeSet));
    document.querySelectorAll('[data-font-set]').forEach(b => b.setAttribute('aria-pressed', (d.dataset.font || 'sans') === b.dataset.fontSet));
  };
  let t; const idle = () => { d.classList.remove('idle'); clearTimeout(t); t = setTimeout(() => d.classList.contains('reading') && d.classList.add('idle'), 2200); };
  const toggle = on => { on = on ?? !d.classList.contains('reading'); d.classList.toggle('reading', on); s.on = on; save(); sync(); if (on) { idle(); scrollTo({ top: 0, behavior: 'instant' }); } };
  document.querySelectorAll('[data-read]').forEach(b => b.addEventListener('click', () => toggle()));
  document.querySelectorAll('[data-theme-set]').forEach(b => b.addEventListener('click', () => { const v = b.dataset.themeSet; if (v === 'light') delete d.dataset.theme; else d.dataset.theme = v; s.theme = v === 'light' ? '' : v; save(); sync(); }));
  document.querySelectorAll('[data-font-set]').forEach(b => b.addEventListener('click', () => { const v = b.dataset.fontSet; if (v === 'sans') delete d.dataset.font; else d.dataset.font = v; s.font = v === 'sans' ? '' : v; save(); sync(); }));
  document.querySelectorAll('[data-size]').forEach(b => b.addEventListener('click', () => { const n = Math.min(28, Math.max(15, base() + +b.dataset.size)); d.style.setProperty('--size', n + 'px'); s.size = n; save(); }));
  addEventListener('keydown', e => {
    if (e.metaKey || e.ctrlKey || e.altKey || /input|textarea/i.test(e.target.tagName)) return;
    const on = d.classList.contains('reading');
    if (e.key === 'r') toggle(); else if (e.key === 'Escape' && on) toggle(false);
    else if (on && (e.key === '+' || e.key === '=')) document.querySelector('[data-size="1"]').click();
    else if (on && e.key === '-') document.querySelector('[data-size="-1"]').click();
  });
  ['mousemove', 'touchstart', 'keydown'].forEach(ev => addEventListener(ev, idle, { passive: true }));
  const bar = document.querySelector('.progress'), art = document.querySelector('article.post');
  const tick = () => { const r = art.getBoundingClientRect(); bar.style.transform = `scaleX(${Math.min(1, Math.max(0, -r.top / Math.max(r.height - innerHeight * .6, 1)))})`; };
  addEventListener('scroll', tick, { passive: true }); tick();
  document.querySelectorAll('.code .copy').forEach(b => b.addEventListener('click', async () => {
    try { await navigator.clipboard.writeText(b.parentElement.querySelector('code').innerText); b.textContent = 'copied'; } catch (e) { b.textContent = 'press ⌘C'; }
    setTimeout(() => b.textContent = 'copy', 1400); }));
  sync(); if (d.classList.contains('reading')) idle();
})();
</script>"""

# Story covers in Freshflo colours, drawn from each post's slug: voice waves, settling lines, the full stop.
PALETTES = [("#e9f8f1", "#0e9f79", "#0c2421", "#bdf0db"), ("#0c2421", "#3ddbab", "#e8f2ef", "#17a884"), ("#eef4f2", "#7d9c95", "#0e9f79", "#0c2421"),
            ("#dff3ea", "#087a5c", "#22c99b", "#f8fbfa"), ("#13302b", "#bdf0db", "#22c99b", "#62e7bf"), ("#f8fbfa", "#b3c2be", "#0e9f79", "#0c2421")]
def art(slug, label=""):
    h = 0
    for ch in slug: h = (h * 131 + ord(ch)) % 2**31
    rnd = lambda n: (h >> n) % 1000 / 1000
    bg, a, b, c = PALETTES[h % len(PALETTES)]
    kind = (h >> 3) % 4
    s = [f'<rect width="400" height="250" fill="{bg}"/>']
    if kind == 0:   # messy line settling into a clean one, then a dot
        pts, x = [], 30
        while x < 230:
            amp = 70 * (1 - (x - 30) / 220)
            pts.append(f"{x},{125 + (amp if len(pts) % 2 else -amp) * (.5 + rnd(len(pts) % 20) / 2):.0f}"); x += 18
        s.append(f'<polyline points="{" ".join(pts)} 300,125" fill="none" stroke="{a}" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>')
        s.append(f'<circle cx="340" cy="125" r="13" fill="{c}"/>')
    elif kind == 1:  # waveform bars
        for i in range(20):
            v = ((h >> (i % 24)) % 100) / 100
            hh = 24 + v * 150
            s.append(f'<rect x="{26 + i * 18}" y="{125 - hh / 2:.0f}" width="9" height="{hh:.0f}" rx="4.5" fill="{a if i % 6 else c}"/>')
    elif kind == 2:  # ripples from a source
        cx, cy = 80 + rnd(4) * 60, 125
        for i in range(8, 0, -1):
            s.append(f'<circle cx="{cx:.0f}" cy="{cy}" r="{i * 34}" fill="none" stroke="{a if i % 2 else b}" stroke-width="{3 + i % 3}" opacity="{.25 + i * .08:.2f}"/>')
        s.append(f'<circle cx="{cx:.0f}" cy="{cy}" r="16" fill="{c}"/>')
    else:            # lines of text being cleaned up
        for r in range(6):
            y = 46 + r * 32
            w = 140 + rnd(r * 3) * 190
            clean = r >= 3
            s.append(f'<rect x="34" y="{y}" width="{w:.0f}" height="12" rx="6" fill="{a if clean else b}" opacity="{1 if clean else .35}"/>')
            if not clean:
                s.append(f'<path d="M30 {y + 6} q 40 -14 80 0 t 80 0 t 80 0" fill="none" stroke="{c}" stroke-width="3" opacity=".7"/>')
        s.append(f'<circle cx="360" cy="{46 + 5 * 32 + 6}" r="10" fill="{c}"/>')
    return f'<span class="art" role="img" aria-label="{html.escape(label)}"><svg viewBox="0 0 400 250" preserveAspectRatio="xMidYMid slice">{"".join(s)}</svg></span>'

BRAND = '<a class="brand" href="/" aria-label="Freshflo · The Digital Nook, home"><img src="/icon-64.png" alt="" width="32" height="32"><b>freshflo<i>.</i></b><span>The Digital Nook</span></a>'

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
<meta property="og:image" content="{APP}/og.png"><meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#f8fbfa">
<link rel="canonical" href="{SITE}{path}">
<link rel="alternate" type="application/rss+xml" title="{NAME}" href="/feed.xml">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png"><link rel="icon" href="/icon.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="/apple-touch-icon.png">
{BOOT}
{FONTS}
<style>{CSS}</style>
</head>
<body>
<header class="top"><div class="in">{BRAND}
<nav aria-label="Main"><a class="hide-sm" href="/#story">The story</a><a class="hide-md" href="/#stories">Stories</a><a class="hide-md" href="/archive">Archive</a><a class="pill" href="{APP}/welcome">Get Freshflo</a></nav></div></header>
<div class="wrap">
{body}
<footer>{BRAND}<span><a href="/about">About</a> · <a href="/archive">Archive</a> · <a href="/feed.xml">RSS</a> · <a href="{APP}">freshflo.vercel.app</a></span></footer>
</div>
{script}
</body>
</html>
"""

# ---------- Build ----------
iso = lambda d: d.isoformat()
nice = lambda d: d.strftime("%-d %B %Y")
short = lambda d: d.strftime("%-d %b")
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
chron = list(reversed(essays))                     # chapter 1 = the first story written
for n, p in enumerate(chron, 1): p["chapter"] = n

if os.path.isdir(OUT):
    for x in os.listdir(OUT):
        if x != ".vercel": shutil.rmtree(os.path.join(OUT, x)) if os.path.isdir(os.path.join(OUT, x)) else os.remove(os.path.join(OUT, x))
os.makedirs(os.path.join(OUT, "p"), exist_ok=True)
for f in glob.glob(os.path.join(ROOT, "static", "*")): shutil.copy(f, OUT)

READBAR = """<div class="rbar" role="toolbar" aria-label="Reading settings">
  <button type="button" data-size="-1" aria-label="Smaller text">A−</button><button type="button" data-size="1" aria-label="Larger text">A+</button>
  <span class="sep"></span>
  <button type="button" data-font-set="sans">Sans</button><button type="button" data-font-set="serif">Serif</button>
  <span class="sep"></span>
  <button type="button" data-theme-set="light" aria-label="Light"><span class="sw" style="background:#f8fbfa"></span></button><button type="button" data-theme-set="sepia" aria-label="Sepia"><span class="sw" style="background:#f6f0e4"></span></button><button type="button" data-theme-set="dark" aria-label="Dark"><span class="sw" style="background:#0b1311"></span></button>
  <span class="sep"></span>
  <button type="button" data-read aria-label="Leave reading mode">✕<span class="hide-sm">&nbsp;Exit</span></button>
</div>"""

def card(p, lead=False):
    return (f'<a class="card{" lead" if lead else ""}" href="/p/{p["slug"]}">{art(p["slug"])}<div class="body">'
            f'<p class="eyebrow"><b>Chapter {p["chapter"]}</b> · {short(p["date"])}</p><h3>{html.escape(p["title"])}</h3>'
            f'<p>{html.escape(p["summary"])}</p><span class="foot">{p["mins"]} min read →</span></div></a>')

CTA = f"""<section class="cta"><img src="/icon-512.png" alt="Freshflo app icon" width="88" height="88">
  <div><h2>Say it messy. <em>Send it fresh.</em></h2><p>This is the app being built in these pages. Free while it's in beta, for Mac, Windows and Android.</p></div>
  <a class="pill" href="{APP}/welcome">Try Freshflo →</a></section>"""

for i, p in enumerate(chron):
    prev, nxt = (chron[i - 1] if i else None), (chron[i + 1] if i + 1 < len(chron) else None)
    nav = '<nav class="chapnav" aria-label="Chapters">' \
        + (f'<a href="/p/{prev["slug"]}"><span class="eyebrow">← Chapter {prev["chapter"]}</span><b>{html.escape(prev["title"])}</b></a>' if prev else '<a href="/#story"><span class="eyebrow">← The story so far</span><b>See every chapter</b></a>') \
        + (f'<a class="n" href="/p/{nxt["slug"]}"><span class="eyebrow">Chapter {nxt["chapter"]} →</span><b>{html.escape(nxt["title"])}</b></a>' if nxt else f'<a class="n" href="/#next"><span class="eyebrow">Up next →</span><b>{html.escape(STORY["launch"])}</b></a>') + "</nav>"
    body = f"""<div class="progress" aria-hidden="true"></div>
{READBAR}
<main>
  <header class="a-head">
    <p class="eyebrow chap">{mark()}<span><b>Chapter {p["chapter"]} of {len(chron)}</b> · {nice(p["date"])}</span></p>
    <h1>{html.escape(p["title"])}</h1>
    {f'<p class="dek">{html.escape(p["summary"])}</p>' if p["summary"] else ""}
    <div class="a-meta"><span>{p["mins"]} min read</span><span>{p["words"]:,} words</span>
      <button class="btn btn-read" type="button" data-read>Reading mode <kbd>R</kbd></button></div>
  </header>
  <figure class="hero-art" style="margin:0 auto">{art(p["slug"], "Story illustration")}</figure>
  <article class="post">
{p["body"]}
    <div class="end" aria-hidden="true">{mark()}</div>
  </article>
  {nav}
  {CTA}
</main>"""
    open(os.path.join(OUT, "p", p["slug"] + ".html"), "w").write(page(f'{p["title"]} — {NAME}', p["summary"], f'/p/{p["slug"]}', body, POST_JS))

# Home: the story of Freshflo
road = STORY["roadmap"]
done = sum(r["status"] == "done" for r in road)
pct = round(100 * (done + .5 * sum(r["status"] == "doing" for r in road)) / len(road))
day = (date.today() - date.fromisoformat(STORY["started"])).days
by_date = {}
for p in chron: by_date.setdefault(iso(p["date"]), p)
chapters = []
for n, m in enumerate(STORY["milestones"], 1):
    p = by_date.get(m["date"])
    link = f'<a class="read" href="/p/{p["slug"]}">Read: {html.escape(p["title"])} →</a>' if p else ""
    chapters.append(f'<li data-n="{n:02d}"><time datetime="{m["date"]}">{nice(date.fromisoformat(m["date"]))}</time><h3>{html.escape(m["title"])}</h3><p>{html.escape(m["text"])}</p>{link}</li>')
left = "".join(f'<span class="{r["status"]}">{html.escape(r["item"])}</span>' for r in road if r["status"] != "done")
chapters.append(f'<li class="next" id="next"><time>Next</time><h3>The road to <em>{html.escape(STORY["launch"])}</em></h3><p>{done} of {len(road)} launch goals are done. Still to go:</p><div class="left">{left}</div></li>')
first = chron[0] if chron else None
latest = chron[-1] if chron else None
home = f"""<main>
  <section class="hero">
    <div>
      <p class="eyebrow"><b>The Digital Nook</b> · behind the scenes</p>
      <h1>The story of building <em>Freshflo</em>.</h1>
      <p class="lede">A dictation app made in the open. Every bug, measurement and decision on the way to launch, written down while it happens.</p>
      <div class="actions">{f'<a class="pill" href="/p/{first["slug"]}">Start at chapter one →</a>' if first else ""}{f'<a class="pill ghost" href="/p/{latest["slug"]}">Read the latest</a>' if latest else ""}</div>
    </div>
    <figure class="tile" style="margin:0">{mark()}
      <div class="demo" aria-label="Freshflo turns messy speech into clean text">
        <p class="said"><span class="rec"></span><span class="txt">so um I think we should uh ship it friday no wait thursday</span></p>
        <p class="sent"><span class="ok">✓</span><span class="txt">I think we should ship it Thursday.</span></p>
      </div>
      <figcaption>say it messy, send it fresh</figcaption></figure>
  </section>
  <div class="stats">
    <div><b data-since="{STORY["started"]}">{day}</b><span>days building</span></div>
    <div><b>{len(essays)}</b><span>chapters written</span></div>
    <div><b>{len(notes)}</b><span>dispatches</span></div>
    <div><b>{pct}%</b><div class="bar"><i style="width:{pct}%"></i></div><span>of the way to launch</span></div>
  </div>
  <section class="sec" id="story">
    <div class="sec-head"><div><p class="eyebrow"><b>The story so far</b></p><h2>From a messy first line to a clean launch.</h2></div><p>Freshflo's mark is a scribble that settles into one clean stroke. The journey looks the same.</p></div>
    <ol class="chapters">{"".join(chapters)}</ol>
  </section>
  <section class="sec" id="stories">
    <div class="sec-head"><div><p class="eyebrow"><b>Stories</b></p><h2>Every chapter, in full.</h2></div><a class="pill ghost" href="/archive">Archive →</a></div>
    <div class="stories">{"".join(card(p, lead=(k == 0)) for k, p in enumerate(essays))}</div>
  </section>
  <section class="sec" id="dispatches">
    <div class="sec-head"><div><p class="eyebrow"><b>Dispatches</b></p><h2>Short notes from the workbench.</h2></div></div>
    <div class="disp">{"".join(f'<article id="{n["slug"]}"><p class="eyebrow">{nice(n["date"])}</p><h3>{html.escape(n["title"])}</h3>{n["body"]}</article>' for n in notes)}</div>
  </section>
  {CTA}
</main>
<script>(function(){{var d=document.querySelector('.demo');if(!d)return;var L=[["so um I think we should uh ship it friday no wait thursday","I think we should ship it Thursday."],["okay so the the mic was silent because like the device changed","The mic went silent because the input device changed."],["remind me to um email the beta folks tomorrow morning","Email the beta testers tomorrow morning."]],i=0,said=d.querySelector('.said .txt'),sent=d.querySelector('.sent .txt');if(matchMedia('(prefers-reduced-motion: reduce)').matches){{d.classList.add('done');return}}function run(){{var w=L[i][0].split(' '),k=0;d.classList.remove('done');said.textContent='';sent.textContent=L[i][1];(function t(){{if(k<w.length){{said.textContent+=(k?' ':'')+w[k++];setTimeout(t,110)}}else{{setTimeout(function(){{d.classList.add('done')}},350);i=(i+1)%L.length;setTimeout(run,4200)}}}})()}}run()}})();</script>
<script>document.querySelectorAll('[data-since]').forEach(b => b.textContent = Math.floor((Date.now() - new Date(b.dataset.since)) / 864e5));</script>"""
open(os.path.join(OUT, "index.html"), "w").write(page(f"{NAME} · The story of building Freshflo", TAGLINE, "/", home))

rows = "".join(f'<li class="arow"><span class="eyebrow">{nice(p["date"])}</span><a href="{"/p/" + p["slug"] if not p["note"] else "/#" + p["slug"]}">{html.escape(p["title"])}</a><span class="eyebrow"><b>{"Dispatch" if p["note"] else "Chapter " + str(p["chapter"])}</b></span></li>' for p in posts)
archive = f"""<main><header class="a-head"><p class="eyebrow"><b>Archive</b></p><h1>Everything, in order.</h1></header>
<style>.arow {{ display: grid; grid-template-columns: 150px 1fr auto; gap: 18px; align-items: baseline; padding: 18px 0; border-bottom: 1px solid var(--line); }} .arow a {{ font: 400 1.6rem/1.2 var(--serif); color: var(--ink); text-decoration: none; }} .arow a:hover {{ color: var(--fresh-ink); }} @media (max-width: 640px) {{ .arow {{ grid-template-columns: 1fr; gap: 4px; }} }}</style>
<ul style="list-style:none;padding:0;max-width:860px;margin:0 auto">{rows}</ul></main>"""
open(os.path.join(OUT, "archive.html"), "w").write(page(f"Archive — {NAME}", "Every chapter and dispatch.", "/archive", archive))

about = f"""<main>
  <header class="a-head"><p class="eyebrow"><b>About</b></p><h1>The work behind <em>Freshflo</em>.</h1>
  <p class="dek">The Digital Nook is Freshflo's behind-the-scenes journal.</p></header>
  <article class="post">
<p>Most products only show the finished thing. This is the part in between: the bugs that took too long to find, the numbers behind each decision, and the questions still open on the way to launch.</p>
<p><a href="{APP}">Freshflo</a> is a dictation app for Mac, Windows and Android. You say it messy; it hands back the clean version you meant.</p>
<h2 id="read">Made for reading</h2>
<p>Every chapter has a <strong>reading mode</strong>. Press <code>R</code> and everything but the words disappears; pick the text size, sans or serif, and a light, sepia or dark page. It remembers your choice.</p>
<p>The site is plain HTML built from Markdown files by one small script. No trackers, no cookies. Follow along by <a href="/feed.xml">RSS</a>.</p>
  </article>
  {CTA}
</main>"""
open(os.path.join(OUT, "about.html"), "w").write(page(f"About — {NAME}", "The Digital Nook is Freshflo's behind-the-scenes journal.", "/about", about))
open(os.path.join(OUT, "404.html"), "w").write(page(f"Not found — {NAME}", "Page not found.", "/404", f'<main><header class="a-head"><p class="eyebrow chap">{mark()}<b>404</b></p><h1>This page got lost in the noise.</h1><p class="dek"><a href="/">Back to the story →</a></p></header></main>'))

rfc = lambda d: format_datetime(datetime(d.year, d.month, d.day, tzinfo=timezone.utc))
link = lambda p: f"{SITE}/#{p['slug']}" if p["note"] else f"{SITE}/p/{p['slug']}"
items = "\n".join(f"  <item><title>{html.escape(p['title'])}</title><link>{link(p)}</link><guid>{link(p)}</guid><pubDate>{rfc(p['date'])}</pubDate><description>{html.escape(p['summary'] or re.sub(r'<[^>]+>', '', p['body']))}</description></item>" for p in posts)
open(os.path.join(OUT, "feed.xml"), "w").write(f'<?xml version="1.0" encoding="utf-8"?>\n<rss version="2.0"><channel>\n  <title>{NAME} · Freshflo</title><link>{SITE}</link><description>{html.escape(TAGLINE)}</description>\n{items}\n</channel></rss>\n')
open(os.path.join(OUT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
urls = ["/", "/about", "/archive"] + [f"/p/{p['slug']}" for p in essays]
open(os.path.join(OUT, "sitemap.xml"), "w").write('<?xml version="1.0" encoding="utf-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(f"  <url><loc>{SITE}{u}</loc></url>" for u in urls) + "\n</urlset>\n")
shutil.copy(os.path.join(ROOT, "vercel.json"), os.path.join(OUT, "vercel.json"))
print(f"✓ {NAME}: {len(essays)} chapters, {len(notes)} dispatches, {len(STORY['milestones'])} milestones → dist/")
