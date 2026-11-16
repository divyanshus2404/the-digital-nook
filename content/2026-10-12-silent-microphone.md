---
title: The case of the silent microphone
date: 2026-10-12
summary: Dictation recorded nothing whenever AirPods were connected. The fix changed how Freshflo picks a mic.
tags: bugs, release
---
For a while, Freshflo sometimes said "the microphone is silent" and meant it: zero audio. It took a while to see the pattern. It happened when AirPods were connected.

## What was going on

The Mac's default input was the AirPods. When Bluetooth headphones switch into microphone mode, audio quality drops and, on some setups, the app got no samples at all.

## The fix

In 0.12.1 Freshflo stopped blindly trusting the system default:

- It ranks the available microphones and prefers the built-in one when that will sound better.
- It never picks a loopback device (the kind used for screen recording) by itself.
- If your mic changes mid-dictation, the audio already recorded carries over to the new mic, so nothing is lost.

Later the recorder moved to a different macOS audio API entirely, because the old one still got silence from the built-in mic while headphones were the output.

> **Tip:** there's now a [microphone guide](https://freshflo.online/microphones) if you want to pick yours by hand.
