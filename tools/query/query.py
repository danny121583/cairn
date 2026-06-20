#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import sys


def parse_filter(f_str):
    if "=" not in f_str:
        return ("text", f_str)
    key, val = f_str.split("=", 1)
    return (key.strip(), val.strip())


def matches_concept(key, meta, filters):
    for f_key, f_val in filters:
        if f_key == "text":
            # Free text search across key, title, description
            text_pool = f"{key} {meta.get('title', '')} {meta.get('description', '')}".lower()
            if f_val.lower() not in text_pool:
                return False
        elif f_key in ("tag", "tags"):
            if f_val not in (meta.get("tags") or []):
                return False
        elif f_key.startswith("relation:"):
            # Check rel_context fields, e.g. relation:strength=hard
            sub_key = f_key.split(":", 1)[1]
            found = False
            for rel in meta.get("relations", []) or []:
                ctx = rel.get("rel_context") or {}
                if str(ctx.get(sub_key)) == f_val:
                    found = True
                    break
            if not found:
                return False
        elif f_key in ("relation", "relations", "target"):
            found = False
            for rel in meta.get("relations", []) or []:
                if f_val in str(rel.get("target", "")):
                    found = True
                    break
            if not found:
                return False
        else:
            # Direct metadata field match
            if str(meta.get(f_key)) != f_val:
                return False
    return True


def query_index(root, filter_strings):
    index_path = Path(root) / "_index.json"
    if not index_path.exists():
        print(f"Error: Index file not found at {index_path}. Run 'cairn index' first.", file=sys.stderr)
        return []
    
    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Error parsing index: {e}", file=sys.stderr)
        return []

    filters = [parse_filter(f) for f in filter_strings]
    results = []
    
    concepts = index.get("concepts", {})
    for key, meta in concepts.items():
        if matches_concept(key, meta, filters):
            results.append((key, meta))
            
    return results


def main(argv=None):
    ap = argparse.ArgumentParser(description="Query the Cairn index using metadata filters.")
    ap.add_argument("filters", nargs="*", help="Filters in key=val or text query format")
    ap.add_argument("--root", default=".", help="Root directory of the Cairn bundle")
    args = ap.parse_args(argv)
    
    results = query_index(args.root, args.filters)
    formatted = [{"path": r[0], "title": r[1].get("title"), "type": r[1].get("type")} for r in results]
    print(json.dumps(formatted, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
