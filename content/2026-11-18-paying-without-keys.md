---
title: Pro, without a single key to copy
date: 2026-11-18
summary: Payments went live, the app unlocks itself, and Freshflo Cloud means nobody has to paste an API key again.
tags: payments, cloud, release
---
This week Freshflo learned to take money. That sounds like one feature. It turned out to be a whole week of them.

## Paying should feel like nothing

The first version emailed you a licence key to paste into the app. It worked, and I hated it. So now Pro belongs to your account, not to a key. You click **Unlock Pro** in the app, pay in your browser, and the app notices by itself and turns Pro on. No copying, no pasting. If you have a second Mac, you sign in there and Pro is waiting.

The first real test was slow: the browser quietly refused to hand control back to the app. The fix was to stop depending on the browser at all. The app now asks the server, every few seconds, "is my purchase done?" and unlocks itself the moment it is.

## The fast version, for everyone

The best Freshflo needed an API key from a speech provider. Most people will never make one, so most people never saw Freshflo at its best. **Freshflo Cloud** fixes that: sign in, and dictation goes through our server, about half a second from letting go of the key to text appearing. Every account gets a free hour. Pro includes it.

The first version took three seconds, because checking your account meant several slow lookups. A small signed pass, valid for ten minutes, brought that close to zero. If the cloud is ever busy or you're offline, Freshflo quietly dictates on your Mac instead. A dictation should never fail because of us.

## Launch date

Everything stays free until **1 December**. After that, dictation stays free and unlimited; Pro adds the cloud, unlimited meeting notes, Command and Ask, and translation. Early friends get 40% off Lifetime with **BETA40**.

## What's next

Notarizing the Mac app, so it opens without a warning. Then the iPhone keyboard, built on the same cloud.
