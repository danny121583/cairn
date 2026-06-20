#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import argparse
import sys

from tools.validate.validate import validate
from tools.auditor.audit import audit


def run_critique(root_path):
    root = Path(root_path).resolve()
    validation_results = validate(root)
    audit_results = audit(root)

    # 1. Check for structural issues
    dirs = [p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")]
    tools_dir = root / "tools"
    if tools_dir.exists() and tools_dir.is_dir():
        dirs.extend([p for p in tools_dir.iterdir() if p.is_dir()])

    structural_gaps = []
    seen_names = {}
    for d in dirs:
        norm_name = d.name.replace("-", "_")
        if norm_name in seen_names:
            other = seen_names[norm_name]
            if other.name != d.name:
                structural_gaps.append(
                    f"Possible duplication: Directories '{d.relative_to(root)}' and '{other.relative_to(root)}' differ only by hyphen/underscore."
                )
        else:
            seen_names[norm_name] = d

    # 2. Compile compliance issues and specification violations
    violations = []
    compliance_roadmap = []

    # Map validation results by path
    val_map = {item["path"]: item for item in validation_results}

    for item in audit_results:
        path = item["path"]
        level = item["level"]
        notes = item["notes"]
        val = val_map.get(path, {"errors": []})

        if level < 5:
            remedies = []
            if "Level 2 requires description, status, and tags" in notes:
                remedies.append("Add description, status, and tags to frontmatter")
            if "Level 3 requires typed relations where relevant" in notes:
                remedies.append("Add relations list referencing related concepts")
            if "Level 4 requires type to resolve to a schema concept" in notes:
                remedies.append("Ensure type field points to a valid concept in schemas/")

            for err in val["errors"]:
                if "broken relation" in err or "missing confidence" in err:
                    remedies.append(f"Fix relation: {err}")

            compliance_roadmap.append({
                "path": path,
                "level": level,
                "remedies": remedies or ["Resolve validation errors to achieve higher compliance level"]
            })

        if val["errors"]:
            violations.append({
                "path": path,
                "errors": val["errors"]
            })

    # Write findings report
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    reports_dir = root / "reports"
    reports_dir.mkdir(exist_ok=True)
    report_path = reports_dir / f"CAIRN_CRITIQUE_{stamp}.md"

    violations_md = ""
    if violations:
        for v in violations:
            violations_md += f"- **[{v['path']}](file://{root}/{v['path']})**:\n"
            for err in v["errors"]:
                violations_md += f"  - [ ] Error: {err}\n"
    else:
        violations_md = "*No specification violations detected! Great job.*\n"

    structural_md = ""
    if structural_gaps:
        for g in structural_gaps:
            structural_md += f"- [ ] {g}\n"
    else:
        structural_md = "*No duplicate directories or structural issues detected.*\n"

    roadmap_md = ""
    if compliance_roadmap:
        for r in compliance_roadmap:
            roadmap_md += f"- **[{r['path']}](file://{root}/{r['path']})** (Current: Level {r['level']}):\n"
            for rem in r["remedies"]:
                roadmap_md += f"  - [ ] {rem}\n"
    else:
        roadmap_md = "*All files have achieved Level 5+ compliance.*\n"

    content = f"""---
type: schemas/audit-report.md
title: Cairn Critique {stamp}
description: Automated critique of compliance levels, structure, and spec alignment for Cairn.
status: active
tags: [critique, audit, report]
timestamp: {datetime.now(timezone.utc).isoformat()}
relations:
  - type: references
    target: tools/critic-agent/AGENT.md
    confidence: declared
---

# Cairn Critique {stamp}

## Executive Summary

This report evaluates the current health of the Cairn bundle.

- Total Concepts Scanned: {len(validation_results)}
- Compliant (Level 5+): {len(validation_results) - len(compliance_roadmap)}
- Below Target Level: {len(compliance_roadmap)}
- Specification Violations: {len(violations)}

## Specification Violations

These errors must be resolved to achieve standard-compliant validation:

{violations_md}
## Aesthetic & Structural Gaps

These findings identify duplicate dirs or files that should be cleaned up:

{structural_md}
## Compliance Roadmap

The following concepts are below Level 5. Apply the corresponding remedies to upgrade them:

{roadmap_md}
"""

    report_path.write_text(content, encoding="utf-8")
    return report_path, len(violations), len(structural_gaps), len(compliance_roadmap)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run the Cairn Critic Agent.")
    parser.add_argument("root", nargs="?", default=".", help="Root of the Cairn bundle to scan")
    args = parser.parse_args(argv)

    path, violations, structural, roadmap = run_critique(args.root)
    print(f"Critique report written to: {path}")
    print(f"Found {violations} spec violations, {structural} structural issues, and {roadmap} low-compliance concepts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
