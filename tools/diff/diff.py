#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import sys
import yaml


def split_doc(path):
    text = Path(path).read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            return yaml.safe_load(text[4:end]) or {}, text[end + 5 :], True
    return {}, text, False


def diff_relations(old_rels, new_rels):
    old_map = {(r.get("type"), r.get("target")): r for r in old_rels or [] if r.get("type") and r.get("target")}
    new_map = {(r.get("type"), r.get("target")): r for r in new_rels or [] if r.get("type") and r.get("target")}
    
    added = []
    removed = []
    modified = []
    
    for key in set(new_map) - set(old_map):
        added.append(new_map[key])
        
    for key in set(old_map) - set(new_map):
        removed.append(old_map[key])
        
    for key in set(old_map) & set(new_map):
        old_rel = old_map[key]
        new_rel = new_map[key]
        if old_rel != new_rel:
            modified.append((old_rel, new_rel))
            
    return added, removed, modified


def calculate_impact(root, concept_path):
    index_path = Path(root) / "_index.json"
    if not index_path.exists():
        return []
    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
        backlinks = index.get("backlinks", {})
        # Normalize relative path key
        key = Path(concept_path).resolve().relative_to(Path(root).resolve()).as_posix()
        return backlinks.get(key, [])
    except Exception:
        return []


def run_diff(old_file, new_file, root="."):
    o_path = Path(old_file)
    n_path = Path(new_file)
    if not o_path.exists():
        raise FileNotFoundError(f"Original file does not exist: {old_file}")
    if not n_path.exists():
        raise FileNotFoundError(f"New file does not exist: {new_file}")
        
    old_meta, _, old_ok = split_doc(old_file)
    new_meta, _, new_ok = split_doc(new_file)
    
    if not old_ok or not new_ok:
        raise ValueError("Both files must be valid Cairn concepts with frontmatter.")
        
    lines = [f"Semantic Diff: {old_file} -> {new_file}", ""]
    
    # 1. Compare Scalar Fields
    scalars = ["title", "description", "type", "status", "timestamp"]
    has_scalar_changes = False
    for field in scalars:
        old_val = old_meta.get(field)
        new_val = new_meta.get(field)
        if old_val != new_val:
            lines.append(f"  Field '{field}':")
            lines.append(f"    - {old_val}")
            lines.append(f"    + {new_val}")
            has_scalar_changes = True
            
    if has_scalar_changes:
        lines.append("")
        
    # 2. Compare Relations
    added_rels, removed_rels, modified_rels = diff_relations(old_meta.get("relations"), new_meta.get("relations"))
    
    if added_rels:
        lines.append("  Relations Added:")
        for rel in added_rels:
            lines.append(f"    + {rel.get('type')} -> {rel.get('target')} ({rel.get('confidence')})")
        lines.append("")
        
    if removed_rels:
        lines.append("  Relations Removed:")
        for rel in removed_rels:
            lines.append(f"    - {rel.get('type')} -> {rel.get('target')} ({rel.get('confidence')})")
        lines.append("")
        
    if modified_rels:
        lines.append("  Relations Modified:")
        for old_rel, new_rel in modified_rels:
            lines.append(f"    ~ {old_rel.get('type')} -> {old_rel.get('target')}:")
            lines.append(f"      old: {json.dumps(old_rel)}")
            lines.append(f"      new: {json.dumps(new_rel)}")
        lines.append("")
        
    # 3. Downstream Impact
    impacted = calculate_impact(root, old_file)
    if impacted:
        lines.append("  Downstream Impact (Blast Radius):")
        for item in impacted:
            lines.append(f"    <- {item.get('source')} ({item.get('type')}, {item.get('confidence')})")
        lines.append(f"  Total Downstream Dependencies Affected: {len(impacted)}")
    else:
        lines.append("  No downstream dependencies affected (isolated concept).")
        
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Semantically diff two Cairn concepts.")
    ap.add_argument("old_file", help="Original concept file path")
    ap.add_argument("new_file", help="New concept file path")
    ap.add_argument("--root", default=".", help="Root directory of the Cairn bundle")
    args = ap.parse_args(argv)
    
    try:
        out = run_diff(args.old_file, args.new_file, args.root)
        print(out, end="")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
