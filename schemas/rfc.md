---
type: schemas/schema.md
title: RFC
description: A schema for proposed or accepted changes to Cairn.
status: active
tags: [schema, governance]
timestamp: 2026-06-20T00:00:00-05:00
relations:
  - type: references
    target: concept.md
    confidence: declared
    note: The base concept schema that RFC concepts must extend.
---

# RFC Schema

## Required Fields

- `type`
- `title`

## Optional Fields

- `description`
- `status`
- `tags`
- `timestamp`
- `relations`

## Expected Fields

- `status`: `draft` while proposed, `active` after acceptance, `deprecated` if replaced.
