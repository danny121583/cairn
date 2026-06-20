from pathlib import Path
import json
import random
import shutil
import subprocess
import sys
import tempfile
import unittest

from tools.auditor.audit import audit
from tools.index.index import main as write_index
from tools.merge.merge import body_hash, canonical_body, merge_docs
from tools.validate.validate import validate


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
VECTORS = ROOT / "test-vectors"


class CairnToolTests(unittest.TestCase):
    def test_valid_bundle_passes_validation(self):
        results = validate(FIXTURES / "valid-bundle")
        self.assertTrue(results)
        self.assertTrue(all(item["valid"] for item in results), results)

    def test_invalid_bundle_reports_expected_failures(self):
        results = {item["path"]: item for item in validate(FIXTURES / "invalid-bundle")}
        self.assertIn("missing-title.md", results)
        self.assertIn("missing title", results["missing-title.md"]["errors"])
        self.assertIn("broken relation target: missing.md", results["broken-relation.md"]["errors"])
        self.assertIn("relation missing valid confidence: schemas/concept.md", results["bad-confidence.md"]["errors"])
        self.assertIn("hash mismatch", results["hash-mismatch.md"]["errors"])
        self.assertIn("ambiguous alias: shared-old.md", results["alias-a.md"]["errors"])
        self.assertIn("ambiguous alias: shared-old.md", results["alias-b.md"]["errors"])

    def test_index_writes_concepts_and_backlinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            subprocess.run(["cp", "-R", str(FIXTURES / "valid-bundle") + "/.", str(target)], check=True)
            index = write_index(target)
            self.assertIn("service.md", index["concepts"])
            self.assertIn("database.md", index["backlinks"])
            written = json.loads((target / "_index.json").read_text(encoding="utf-8"))
            self.assertEqual(written["concepts"]["service.md"]["title"], "Service")

    def test_cli_validate_and_audit_json_only(self):
        validate_cmd = [sys.executable, str(ROOT / "cairn_cli.py"), "validate", str(FIXTURES / "valid-bundle")]
        self.assertEqual(subprocess.run(validate_cmd, cwd=ROOT, capture_output=True).returncode, 0)

        audit_cmd = [sys.executable, str(ROOT / "cairn_cli.py"), "audit", str(FIXTURES / "valid-bundle"), "--json-only"]
        completed = subprocess.run(audit_cmd, cwd=ROOT, text=True, capture_output=True, check=True)
        payload = json.loads(completed.stdout)
        self.assertIsNone(payload["report"])
        self.assertGreaterEqual(len(payload["results"]), 1)

    def test_migration_scanner_stages_report_without_touching_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "run"
            cmd = [
                sys.executable,
                str(ROOT / "cairn_cli.py"),
                "migrate",
                str(FIXTURES / "sample-project"),
                "--output",
                str(output),
            ]
            completed = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=True)
            summary = json.loads(completed.stdout)
            self.assertFalse(summary["source_modified"])
            self.assertTrue(Path(summary["report"]).exists())
            self.assertTrue((output / "cairn-proposed").exists())

    def test_hash_vectors_match_python_and_javascript(self):
        vectors = json.loads((VECTORS / "hash-vectors.json").read_text(encoding="utf-8"))
        node = shutil.which("node")
        for vector in vectors:
            self.assertEqual(canonical_body(vector["document"]), vector["canonical_body"])
            self.assertEqual(body_hash(vector["canonical_body"]), vector["sha256"])
            if node:
                with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as fh:
                    fh.write(vector["document"])
                    path = fh.name
                try:
                    completed = subprocess.run(
                        [node, str(ROOT / "js" / "cairn.js"), "hash", path],
                        text=True,
                        capture_output=True,
                        check=True,
                    )
                    self.assertEqual(completed.stdout.strip(), vector["sha256"])
                finally:
                    Path(path).unlink(missing_ok=True)

    def test_merge_vectors(self):
        vectors = json.loads((VECTORS / "merge-vectors.json").read_text(encoding="utf-8"))
        for vector in vectors:
            meta, body, conflicts = merge_docs(vector["base"], vector["ours"], vector["theirs"])
            self.assertEqual(meta["description"], vector["expected_description"])
            self.assertEqual(meta["tags"], vector["expected_tags"])
            self.assertEqual(conflicts, vector["expected_conflicts"])
            self.assertEqual(meta["hash"], body_hash(body))

    def test_merge_is_deterministic_for_generated_inputs(self):
        rng = random.Random(20260620)
        statuses = ["draft", "active", "deprecated"]
        for idx in range(100):
            base = f"""---
type: schemas/concept.md
title: Concept {idx}
description: Base
status: draft
tags: [base]
timestamp: 2026-06-20T00:00:00Z
---
# Concept {idx}
"""
            ours_tag = rng.choice(["api", "worker", "data"])
            theirs_tag = rng.choice(["api", "service", "docs"])
            ours = base.replace("description: Base", f"description: Ours {idx}").replace("tags: [base]", f"tags: [base, {ours_tag}]").replace("status: draft", f"status: {rng.choice(statuses)}").replace("00:00:00Z", "01:00:00Z")
            theirs = base.replace("description: Base", f"description: Theirs {idx}").replace("tags: [base]", f"tags: [base, {theirs_tag}]").replace("status: draft", f"status: {rng.choice(statuses)}").replace("00:00:00Z", "02:00:00Z")
            first = merge_docs(base, ours, theirs)
            second = merge_docs(base, ours, theirs)
            self.assertEqual(first, second)
            self.assertEqual(first[2], [])

    def test_compliance_vectors(self):
        vectors = json.loads((VECTORS / "compliance-vectors.json").read_text(encoding="utf-8"))
        for vector in vectors:
            bundle = ROOT / vector["bundle"]
            result = next(item for item in validate(bundle) if item["path"] == vector["path"])
            self.assertEqual(result["valid"], vector["valid"])
            if "expected_error" in vector:
                self.assertIn(vector["expected_error"], result["errors"])
            if vector.get("valid"):
                audit_result = next(item for item in audit(bundle) if item["path"] == vector["path"])
                self.assertGreaterEqual(audit_result["level"], vector["minimum_level"])

    def test_corpus_cli_runs_sample_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / "corpus.json"
            report = root / "report.json"
            config.write_text(json.dumps({
                "projects": [
                    {"label": "sample", "path": str(FIXTURES / "sample-project")}
                ]
            }))
            cmd = [
                sys.executable,
                str(ROOT / "cairn_cli.py"),
                "corpus",
                str(config),
                "--output",
                str(root / "runs"),
                "--report",
                str(report),
            ]
            completed = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=True)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["projects"][0]["label"], "sample")
            self.assertTrue(report.exists())


    def test_query_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            subprocess.run(["cp", "-R", str(FIXTURES / "valid-bundle") + "/.", str(target)], check=True)
            write_index(target)
            
            cmd = [sys.executable, str(ROOT / "cairn_cli.py"), "query", "type=schemas/concept.md", "--root", str(target)]
            completed = subprocess.run(cmd, text=True, capture_output=True, check=True)
            results = json.loads(completed.stdout)
            self.assertGreaterEqual(len(results), 1)
            paths = [r["path"] for r in results]
            self.assertIn("database.md", paths)

    def test_export_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            subprocess.run(["cp", "-R", str(FIXTURES / "valid-bundle") + "/.", str(target)], check=True)
            write_index(target)
            
            for fmt in ["dot", "cypher", "graphql"]:
                cmd = [sys.executable, str(ROOT / "cairn_cli.py"), "export", "--format", fmt, "--root", str(target)]
                completed = subprocess.run(cmd, text=True, capture_output=True, check=True)
                self.assertTrue(len(completed.stdout) > 0)

    def test_diff_cli(self):
        cmd = [
            sys.executable,
            str(ROOT / "cairn_cli.py"),
            "diff",
            str(FIXTURES / "valid-bundle" / "database.md"),
            str(FIXTURES / "valid-bundle" / "service.md")
        ]
        completed = subprocess.run(cmd, text=True, capture_output=True, check=True)
        self.assertIn("Semantic Diff", completed.stdout)


if __name__ == "__main__":
    unittest.main()
