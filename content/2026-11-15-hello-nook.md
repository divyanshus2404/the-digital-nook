---
title: Hello from the nook
date: 2026-11-15
summary: Why this site exists, how it's built, and how to read it comfortably.
tags: meta
---
This is a small corner of the internet for the work behind the work. Most products only show the finished thing. Here you'll find the parts in between: the bugs, the measurements, and the decisions that are still open.

## What lives here

- **Posts:** longer write-ups of one problem, start to finish.
- **Notes:** a few lines when something worth remembering happens.

Most of it is about [Freshflo](https://freshflo.vercel.app) for now, a dictation app on its way to launch.

## Built to be read

Every post has a reading mode. Press `R` and everything except the words disappears. A small toolbar lets you change the text size, switch between sans and serif, and pick a light, sepia or dark page. Your choice is remembered next time.

> **Shortcuts:** `R` toggles reading mode, `+` and `-` change the size, `Esc` leaves.

## How it's made

The whole site is Markdown files and one Python script that turns them into plain HTML:

```bash
python3 build.py && cd dist && vercel deploy --prod
```

No framework, no trackers, no cookies. It loads fast and works without JavaScript.
