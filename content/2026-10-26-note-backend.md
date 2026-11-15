---
title: The server code got its own home
date: 2026-10-26
type: note
tags: infra
---
The API moved into a separate private repository. Nothing reaches production now without a pull request, a review and passing tests. The website build refuses to deploy a backend that isn't exactly the reviewed version.
