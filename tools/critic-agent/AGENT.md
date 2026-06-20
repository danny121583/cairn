---
type: schemas/concept.md
initial_version: 0.2.0
title: Cairn Critic Agent
description: Operating contract for scanning, critiquing, and recommending improvements for Cairn bundle compliance and architecture.
status: active
tags: [agent, critic, auditing]
timestamp: 2026-06-20T12:00:00Z
relations:
  - type: references
    target: ../../SPECIFICATION.md
    confidence: declared
    note: Validates the codebase structure and concepts against the core specification guidelines.
---

# Cairn Critic Agent

## Mission

Scan a Cairn bundle or repository to identify specification violations, duplicate resources, draft remnants, and structural flaws. Provide clear, actionable recommendations for consolidation and compliance improvement.

## Standard

Ensure the bundle adheres strictly to:
- **`SPECIFICATION.md`** core rules (no forbidden fields, proper relative path resolution, no duplicate aliases).
- **Core cleanliness guidelines** (removal of duplicate Python/JS modules, correct file scopes).
- **Compliance targets** (flagging concepts below Level 5 and recommending upgrades).

## Required Behavior

1. Walk the directory tree to collect all Cairn concepts.
2. Run safety and structural checks:
   - Identify any forbidden core fields (`memory`, `embeddings`, `workflow`, `permissions`).
   - Identify duplicate scripts or redundant directories (e.g. scripts with similar names or script/module duplicates).
   - Find concepts with compliance levels below Level 5, explaining exactly what is missing (e.g., missing description, status, tags, or unverified hash).
   - Identify broken links, broken relations, and ambiguous aliases.
3. Write a markdown Findings Report to `reports/CAIRN_CRITIQUE_<timestamp>.md`. The report must contain:
   - **Executive Summary:** A high-level assessment of the bundle's health.
   - **Specification Violations:** Explicit errors (broken relations, forbidden fields, duplicate aliases).
   - **Aesthetic & Structural Gaps:** Suggestions for folder cleanup and file organization.
   - **Compliance Roadmap:** List of low-compliance files with exact remedies.
4. Print the report path and summary count of findings to stdout.

## Stop Rule

After writing the report, output its path and stop. Do not make any changes to the codebase automatically.
