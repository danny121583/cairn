---
type: schemas/specification.md
title: Cairn v0.3.0 Specification
description: Defines the core Cairn format for portable, file-based knowledge concepts.
status: active
tags: [cairn, specification, core]
timestamp: 2026-06-20T00:00:00-05:00
relations:
  - type: implements
    target: RFC/0001-cairn-core.md
    confidence: declared
    note: Establishes the initial Cairn core specification.
---

# Cairn v0.3.0 Specification

## 1. The Cairn Concept

A Cairn concept is a plain markdown file with optional YAML frontmatter. The file path is the concept's identity within a bundle. The body is ordinary markdown and remains useful without any tooling installed.

```yaml
---
type: <reference to a schema concept>
title: <human-readable name>
description: <one to two sentences>
status: draft | active | deprecated
tags: [tag-one, tag-two]
timestamp: <ISO 8601, last modified>
hash: <optional sha256 of the canonical body, for integrity verification>
aliases:
  - <prior file path(s), if this concept was renamed or moved>
relations:
  - type: <depends_on | owns | joins | references | supersedes | implements | ...>
    target: <relative path, or cairn://<bundle-id>/<path> for cross-bundle>
    confidence: declared | inferred
    note: <optional plain-language description>
    rel_context:
      kind: api_call | import | foreign_key | config | file | manual
      strength: hard | soft | optional
    evidence:
      - type: code_extraction | naming_heuristic | user_assertion | ...
        source_uri: <file path or URI>
        line: <line number>
        extract: <source text snippet>
        tool: <scanner name and version>
        extracted_at: <timestamp>
automation_policy:
  agent_modification_allowed: <boolean>
  agent_can_infer_relations: <boolean>
  agent_can_add_evidence: <boolean>
  change_requires_approval: <boolean>
  automation_safe_fields: [<list of fields>]
  approval_gate_team: <team-name>
---

# Body

Ordinary markdown.
```

Only `type` and `title` are required.

Cairn goes further than earlier file-based formats through four structural additions:

1. Relation provenance. Every relation declares `confidence: declared | inferred`, plus an optional `note` for evidence. Prior formats treat all links as equally trustworthy; Cairn lets a graph be queried for exactly which edges are verified versus guessed.
2. Content-addressed integrity. A concept may carry a `hash` of its canonical body. This lets any consumer detect, without a central registry, whether a concept referenced from another bundle has silently changed since it was linked.
3. Deterministic merge rules. Cairn defines exactly how frontmatter merges so a YAML merge conflict has one correct resolution instead of being an ad hoc text conflict.
4. Proof of minimalism. Cairn ships reference parsers under 60 lines, zero dependencies beyond a YAML library, in TypeScript and Python.

## 2. Identity

Within a bundle, a concept's identity is its relative file path from the bundle root. Across bundles, identity is expressed as:

```text
cairn://<bundle-id>/<relative-path>
```

Consumers resolve relative paths first from the referencing concept's directory. If relative resolution fails and the target is a `cairn://` URI, the consumer may resolve it through a known bundle registry, local mount, or configured fetcher. Cairn core does not require any registry.

## 3. Integrity

If `hash` is present, it is the lowercase hexadecimal SHA-256 digest of the concept's body content with frontmatter excluded and line endings canonicalized to LF. The body begins after the closing frontmatter delimiter. If no frontmatter exists, the whole file is the body.

A consumer following a `relations.target` may optionally fetch the target and compare its current canonical body hash to the recorded `hash` on that target concept. This detects drift since the link was made. Absence of `hash` is valid: integrity checking is opt-in, never required.

## 4. Aliases

`aliases` carries old paths forward when a concept is renamed or moved. Any reference to an aliased path resolves to the current file rather than failing as missing. Aliases are bundle-local relative paths. A valid alias points to exactly one current concept; if two concepts claim the same alias, the alias is ambiguous and invalid for Level 5 compliance.

## 5. Relations

Relations are typed, structured edges:

```yaml
relations:
  - type: depends_on
    target: services/payment.md
    confidence: declared
    note: Human-reviewed dependency.
    rel_context:
      kind: api_call
      strength: hard
    evidence:
      - type: code_extraction
        source_uri: "file://src/payment.ts"
        line: 12
        extract: "import { PaymentStatus } from 'types/shared'"
        tool: cairn-code-scanner/v2.1
        extracted_at: 2026-06-20T14:32:00Z
```

`declared` means a human asserted the relation. `inferred` means a tool derived it from evidence such as an import statement, foreign key, manifest, route, or config dependency. Never mark an inferred relation as `declared`. Inferred relations should include a `note` citing concrete evidence, and optionally structure their findings under `rel_context` and `evidence`.

Common relation types include `depends_on`, `owns`, `joins`, `references`, `supersedes`, and `implements`. A bundle may define additional types in schema concepts or companion specifications.

## 6. Schema Contracts

A `type` value is itself a Cairn concept under `schemas/`. A schema concept documents required, optional, and forbidden fields for that type. Cairn validates itself: no external schema language is required. Schema concepts version, deprecate, and relate like any other concept.

Schema contracts are descriptive and inspectable. Tools may read them to validate concepts, but humans can also review the contract directly in markdown.

## 7. Lifecycle & Deprecation

`status` is the only lifecycle field in core. Valid values are `draft`, `active`, and `deprecated`. History lives in `git log <path>`. Replacement is modeled with a `supersedes` relation from the replacement concept to the concept it replaces.

For detailed deprecation roadmaps, concepts should implement the optional `deprecation` block defined in [schemas/lifecycle.md](schemas/lifecycle.md).

## 8. Automation Policy

The optional `automation_policy` field defines the permissions and boundaries of autonomous software agents or pipelines acting on the concept. This allows explicit control over what automated processes may read, modify, or suggest for any concept file.

## 9. Merge Rules

When concurrent edits modify the same concept file, merge frontmatter mechanically:

1. Parse all versions into frontmatter maps and markdown bodies.
2. For scalar fields `title`, `description`, and `status`, keep the value from the version with the later `timestamp`. If timestamps are equal or absent, leave a conflict for human review.
3. For `tags`, produce a sorted union of unique strings.
4. For `aliases`, produce a sorted union of unique paths. If the same alias is claimed by another concept elsewhere in the bundle, validation reports it as ambiguous.
5. For `relations`, deduplicate by the `(type, target)` tuple. If duplicate entries have identical tuples, keep the entry from the later `timestamp`. If timestamps are equal or absent, merge non-conflicting fields and leave conflicts on incompatible `confidence` or `note` values.
6. For `hash`, recompute after the final body is chosen. If the body still has a text conflict, remove `hash` or leave a conflict for human review.
7. Body conflicts remain ordinary git markdown conflicts unless a project-specific merge driver is installed.

These rules are precise enough for a git merge driver: relation identity is `(type, target)`, scalar conflict authority is the concept-level `timestamp`, and array fields have deterministic set behavior.

## 9. Compliance Levels

Compliance is reported per concept. Never collapse compliance into one repository or bundle score.

| Level | Requirement |
|---|---|
| 1 | `type` + `title` |
| 2 | + `description`, `status`, `tags` |
| 3 | + at least one typed `relations` entry where relevant |
| 4 | + `type` resolves to an existing schema concept |
| 5 | + every relation carries `confidence`; zero broken relations or orphaned aliases |
| 6 | + `hash` present and verified against current body content |

## 10. Out of Scope

Memory, embeddings, workflows, and permissions are out of scope for Cairn core. These belong in separate, independently versioned companion layers that reference Cairn concepts by path or `cairn://` URI. Core must not add memory, embedding, workflow, or permission fields.

## Reference Tooling

`tools/validate/` reports per-concept pass/fail against the matching schema concept, checks relation and alias resolution, and verifies hashes where present. It never emits a bundle-wide compliance score.

`tools/index/` generates `_index.json` from all frontmatter for fast structured queries. It includes computed backlinks, regenerated from forward relations and never hand-edited.

`tools/auditor/` reads `schemas/audit-rubric.md`; the scoring methodology is a published Cairn concept, inspectable and versionable like everything else.

`tools/reference-parser/` contains TypeScript and Python parsers for the core format under 60 lines each, with no dependency beyond a YAML library. These files are the proof artifact for Cairn's minimalism claim.

## Project Analysis Workflow

Cairn migration tooling operates read-only by default. It never modifies a source repository being analyzed unless explicitly instructed.

1. Scan candidate concepts: services, modules, APIs, data models, workflows, ownership files, and existing docs.
2. Generate candidates into a staging directory such as `cairn-proposed/`, never overwriting source. Descriptions come only from existing source text; otherwise use `<needs author input>`. Every inferred relation cites concrete evidence in `note`.
3. Score each concept with the published rubric. Never aggregate into one project-wide number.
4. Report to `reports/CAIRN_MIGRATION_<timestamp>.md`, itself a valid Cairn concept with `type: Migration Report`, covering Current State, Knowledge Inventory, Relationship Inventory split by confidence, Per-Concept Compliance Levels, Gaps, and a Migration Roadmap.
5. Stop and let a human decide what to merge into the real project.
