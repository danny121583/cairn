---
type: schemas/concept.md
title: Cairn Migration Agent Contract
description: Operating contract for an agent that scans projects and stages Cairn migration artifacts.
status: active
tags: [agent, migration, cairn]
timestamp: 2026-06-20T09:46:00-05:00
relations:
  - type: implements
    target: ../../migration-guides/project-analysis.md
    confidence: declared
    note: Defines the agent behavior required by the project analysis workflow.
  - type: references
    target: README.md
    confidence: declared
    note: Companion documentation for the runnable implementation.
---

# Cairn Migration Agent Contract

## Mission

Scan any project and stage a Cairn migration without modifying source files by default.

## Non-Negotiable Rules

- Read the source project as evidence; do not invent descriptions.
- Write generated concepts to a staging directory, not over source files.
- Use `<needs author input>` when source text does not support a claim.
- Mark every generated relation as `confidence: inferred`.
- Cite evidence for every inferred relation using a concrete file, line, import, foreign key, or config key.
- Report compliance per concept only.
- Write reports under `reports/` with timestamped filenames.
- Stop after presenting staged artifacts; a human decides what to merge.

## Output Contract

The agent produces:

- `cairn-proposed/`: staged concept files.
- `cairn-proposed/schemas/concept.md`: copied base schema for local validation.
- `reports/CAIRN_MIGRATION_<timestamp>.md`: migration report as a Cairn concept.

## Review Contract

Before staged concepts become project truth, a human reviews:

- titles
- descriptions
- ownership
- inferred relation targets
- relation confidence
- whether project-specific schema concepts are needed
