---
type: schemas/schema.md
title: Concept
description: The base schema contract for a Cairn concept file.
status: active
tags: [schema, core]
timestamp: 2026-06-20T00:00:00-05:00
relations:
  - type: references
    target: schema.md
    confidence: declared
    note: The base meta-schema from which concept schemas derive.
---

# Concept Schema

## Required Fields

- `type`: path or URI resolving to a schema concept
- `title`: human-readable concept name

## Optional Fields

- `description`: one to two sentence summary
- `status`: `draft`, `active`, or `deprecated`
- `tags`: list of strings
- `timestamp`: ISO 8601 last modified timestamp
- `hash`: SHA-256 of the canonical body
- `aliases`: list of previous bundle-local paths
- `relations`: list of typed relation objects

## Forbidden Fields

- `memory`
- `embeddings`
- `workflow`
- `permissions`

These fields belong in companion layers, not Cairn core.
