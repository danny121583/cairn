# Changelog

## 0.3.0

- Added `rel_context` (kind + strength) to structure relation dependencies.
- Added structured `evidence` arrays to backing inferred relations with proof details.
- Added `automation_policy` configuration for defining autonomous agent boundaries.
- Introduced `cairn query` to filter concept indexes using tags, relations, and context metadata.
- Introduced `cairn export` supporting Graphviz (`dot`), Neo4j (`cypher`), and GraphQL schemas.
- Introduced `cairn diff` to semantically compare concepts and calculate downstream blast-radius.
- Added `schemas/lifecycle.md` and `schemas/validation-rubric.md` schema concepts.

## 0.2.0

- Aligned visible specification and package versions under a standard-candidate version policy.
- Added deterministic `cairn merge` command and executable merge reference implementation.
- Added hash, merge, and compliance test vectors.
- Added randomized merge determinism tests and JavaScript hash parity checks.
- Added npm package metadata and JavaScript reference parser/hash implementation.
- Added URI resolution threat model and migration corpus evaluation harness.

## 0.1.0

- Added installable `cairn` CLI for validate, index, audit, migrate, and parse workflows.
- Added fixture-based regression tests for valid and invalid Cairn bundles.
- Added GitHub Actions CI across Python 3.10, 3.11, and 3.12.
- Added contribution and security guidance.
- Tightened validation so malformed concept-like files are reported instead of skipped.
