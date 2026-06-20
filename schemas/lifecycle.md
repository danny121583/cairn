---
type: schemas/schema.md
title: Lifecycle
description: Schema for defining advanced concept lifecycle, deprecation schedules, and replacement pathways.
status: active
tags: [schema, lifecycle, core]
timestamp: 2026-06-20T00:00:00-05:00
relations:
  - type: references
    target: concept.md
    confidence: declared
    note: Extensions to the core concept metadata schema.
---

# Lifecycle & Deprecation Schema

This schema validates the optional `deprecation` block in Cairn concepts.

## Optional Fields

- `announced_at`: ISO 8601 timestamp when deprecation was announced.
- `sunset_date`: ISO 8601 timestamp when the concept is scheduled to be removed or archived.
- `replacement`: path or URI to the active replacement concept.
- `reason`: short textual reason for deprecation.
- `migration_effort_estimate_days`: estimated number of developer days required to migrate.
- `dependent_concepts_count`: cached count of remaining dependent concepts.
- `blocking_before_removal`: list of blocker issues or task paths that must be completed before removal.
