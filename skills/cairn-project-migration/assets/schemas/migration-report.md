---
type: schemas/schema.md
title: Migration Report
description: A schema for reports produced when analyzing an existing project for Cairn adoption.
status: active
tags: [schema, migration, report]
timestamp: 2026-06-20T00:00:00-05:00
relations:
  - type: references
    target: concept.md
    confidence: declared
    note: The base concept schema that migration report concepts must extend.
---

# Migration Report Schema

## Required Fields

- `type`
- `title`

## Optional Fields

- `description`
- `status`
- `tags`
- `timestamp`
- `relations`

## Required Sections

- Current State
- Knowledge Inventory
- Relationship Inventory
- Per-Concept Compliance Levels
- Gaps
- Migration Roadmap
