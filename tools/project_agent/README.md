---
type: schemas/concept.md
title: Cairn Project Agent
description: A read-only migration agent that scans a project and stages Cairn concepts plus a migration report.
status: active
tags: [tools, migration, agent]
timestamp: 2026-06-20T09:45:00-05:00
relations:
  - type: references
    target: ../../migration-guides/project-analysis.md
    confidence: declared
    note: Implements the read-only project analysis workflow.
  - type: references
    target: ../../schemas/audit-rubric.md
    confidence: declared
    note: Uses the published per-concept compliance model.
---

# Cairn Project Agent

`cairnize.py` scans a project and stages Cairn concepts without modifying the source project by default.

## Run

```sh
python3 tools/project-agent/cairnize.py /path/to/project
```

Default output:

```text
cairn-runs/<project>-<timestamp>/
├── cairn-proposed/
└── reports/CAIRN_MIGRATION_<timestamp>.md
```

To write staging files inside the target project, opt in explicitly:

```sh
python3 tools/project-agent/cairnize.py /path/to/project --write-into-target
```

## Behavior

- Detects candidate services, modules, APIs, data models, workflows, ownership files, and docs.
- Generates staged concept files only; it does not overwrite source files.
- Uses `<needs author input>` when source text does not support a description.
- Marks generated relations as `confidence: inferred`.
- Cites concrete evidence in relation notes using file paths and line numbers when available.
- Writes a timestamped migration report under `reports/`.
- Reports compliance per concept, never as a whole-bundle score.
