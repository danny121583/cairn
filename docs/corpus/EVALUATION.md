---
type: schemas/concept.md
title: Migration Corpus Evaluation
description: Defines how Cairn migration-agent precision and recall should be measured on real projects.
status: active
tags: [corpus, evaluation, migration]
timestamp: 2026-06-20T16:44:00Z
relations:
  - type: references
    target: ../../migration-guides/project-analysis.md
    confidence: declared
    note: The project analysis migration workflow evaluated by this methodology.
---

# Migration Corpus Evaluation

The migration agent's inferred relations should be evaluated as an information-retrieval problem.

## Required Metrics

- Concept candidates detected
- Inferred relations detected
- Relations with concrete source evidence
- Relations requiring `<needs author mapping>`
- False positives against human-labeled ground truth
- False negatives against human-labeled ground truth
- Precision, recall, and F1 after labeling

## Corpus Shape

A useful corpus should include:

- small libraries
- web applications
- monorepos
- mixed-language repositories
- legacy projects with sparse docs
- projects with generated code

## Publication Rule

Do not publish private project paths, private code names, or migration reports from non-public repositories without author review. Public benchmark reports should identify repo URL, commit SHA, scanner version, command line, and labeling method.
