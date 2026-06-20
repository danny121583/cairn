---
type: schemas/concept.md
title: Payment Service
description: Example service concept showing a declared dependency relation.
status: active
tags: [example, service]
timestamp: 2026-06-20T00:00:00-05:00
aliases:
  - examples/billing-service.md
relations:
  - type: depends_on
    target: examples/database.md
    confidence: declared
    note: Maintainer-declared dependency for payment persistence.
    rel_context:
      kind: database
      strength: hard
    evidence:
      - type: code_extraction
        source_uri: "file://src/payment.ts"
        line: 12
        extract: "import { PaymentStatus } from 'types/shared'"
        tool: cairn-code-scanner/v2.1
        extracted_at: 2026-06-20T14:32:00Z
automation_policy:
  agent_modification_allowed: true
  agent_can_infer_relations: true
  agent_can_add_evidence: true
  change_requires_approval: true
  automation_safe_fields: [tags, timestamp]
  approval_gate_team: billing-devs
---

# Payment Service

This is an example Cairn concept for a service. Its relation is declared because a human intentionally asserted it.
