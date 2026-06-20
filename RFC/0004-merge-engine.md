---
type: schemas/rfc.md
title: Executable Merge Semantics
description: Requires deterministic merge semantics to be backed by an executable reference engine and property tests.
status: active
tags: [rfc, merge, testing]
timestamp: 2026-06-20T16:41:00Z
relations:
  - type: implements
    target: ../tools/merge/README.md
    confidence: declared
    note: The Python merge engine is the current executable reference for Cairn merge behavior.
---

# RFC 0004: Executable Merge Semantics

Cairn merge rules are not considered proven by prose alone. The reference repository must include an executable merge engine, deterministic test vectors, and property-style tests for generated inputs.

The current reference engine merges scalar fields by timestamp, unions `tags` and `aliases`, deduplicates relations by `(type, target)`, and recomputes `hash` only when the merged body has no conflict.

Equal timestamp conflicts remain deterministic by emitting stable conflict marker values and returning a non-zero CLI exit status when conflicts exist.
