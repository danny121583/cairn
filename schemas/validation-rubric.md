---
type: schemas/schema.md
title: Validation Rubric
description: Guidelines and methodology for enforcing cross-concept rules and integrity across Cairn bundles.
status: active
tags: [schema, audit, validation]
timestamp: 2026-06-20T00:00:00-05:00
relations:
  - type: references
    target: audit-rubric.md
    confidence: declared
    note: Extensions to the standard concept audit scoring rubric.
---

# Validation Rubric

This concept outlines the methodology for executing and validating complex cross-concept policy rules across a Cairn bundle.

## Cross-Concept Rules

- **Active Services Must Have Active Dependencies:** Active concepts of type `services/**` or `APIs/**` must not depend on `deprecated` targets.
- **APIs Need Test Coverage:** Concepts of type `APIs/**` should have at least one test concept referencing them with an `implements` or `references` relation.
- **No Circular Hard Dependencies:** Transitive paths using `strength: hard` relations must be acyclic.
