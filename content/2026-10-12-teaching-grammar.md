---
title: Teaching dictation how people actually talk
date: 2026-10-12
summary: Version 0.10.0 added a grammar pass for spoken and Indian English. Here's how it's measured.
tags: engineering, release
---
Speech recognition writes down what you said. That's rarely what you meant. "So basically I wanted to, no wait, can we meet Thursday" should become "Can we meet Thursday?"

## Rules first, model second

Freshflo runs a set of deterministic fixes before and after the language model. They handle the patterns that come up again and again in spoken and Indian English, so the model has less to guess.

## Measuring it

Every change is scored against a fixed test set of 76 real spoken sentences. On the day 0.10.0 shipped:

- Cloud cleanup: **76 / 76**
- Apple's on-device model: **75 / 76**
- Offline rules only: **57 / 76**

> **Why offline matters:** it's the mode where nothing leaves your Mac, so it has to be good on its own.

The offline number is the one I'm pushing on.

## What broke along the way

The free tier of the cloud model limits how many tokens it takes per minute, so the test run has to pace itself. When the main model is rate-limited, cleanup now falls back to a second and then a third model instead of failing.
