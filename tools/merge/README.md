---
type: schemas/concept.md
title: Merge Engine
description: Deterministically merges three Cairn concept versions based on field types and timestamps.
status: active
tags: [tools, merge]
timestamp: 2026-06-20T00:00:00-05:00
relations:
  - type: references
    target: ../../RFC/0004-merge-engine.md
    confidence: declared
---

# Merge Engine

The Cairn merge tool provides deterministic 3-way merging of concept documents:

```sh
python tools/merge/merge.py <base> <ours> <theirs> [--output <merged>]
```

It implements the merge logic specified in `RFC/0004-merge-engine.md`.
