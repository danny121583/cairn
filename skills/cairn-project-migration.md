---
type: schemas/agent-skill.md
title: Cairn Project Migration Skill
description: Agent Skills-compatible package for scanning projects and staging Cairn migration artifacts.
status: active
tags: [agent-skills, migration, cairn]
timestamp: 2026-06-20T10:00:00-05:00
relations:
  - type: implements
    target: ../RFC/0002-agent-skills-companion.md
    confidence: declared
    note: Packages Cairn migration behavior as an Agent Skill companion.
  - type: references
    target: ../tools/project_agent/AGENT.md
    confidence: declared
    note: Mirrors the Cairn migration agent operating contract.
---

# Cairn Project Migration Skill

Package path: `skills/cairn-project-migration/`

Primary file: `skills/cairn-project-migration/SKILL.md`

Bundled script: `skills/cairn-project-migration/scripts/cairnize.py`

This skill lets Agent Skills-compatible agents scan a source project read-only, stage Cairn concepts, and write a timestamped migration report.
