---
type: schemas/schema.md
title: Specification
description: A schema for published Cairn specification documents.
status: active
tags: [schema, specification]
timestamp: 2026-06-20T00:00:00-05:00
relations:
  - type: references
    target: concept.md
    confidence: declared
    note: The base concept schema that specification concepts must extend.
---

# Specification Schema

## Required Fields

- `type`
- `title`

## Optional Fields

- `description`
- `status`
- `tags`
- `timestamp`
- `relations`
- `aliases`
- `hash`

## Expected Relations

- `implements`: links the specification to an RFC or governance concept it implements.
