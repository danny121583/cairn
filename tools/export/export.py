#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import re
import sys


def clean_node_id(path):
    return re.sub(r"[^a-zA-Z0-9_]", "_", path)


def to_dot(index):
    lines = ["digraph Cairn {", "  node [shape=box, fontname=\"Helvetica\", fontsize=10];", "  edge [fontname=\"Helvetica\", fontsize=8];", ""]
    concepts = index.get("concepts", {})
    
    # Render nodes
    for path, meta in concepts.items():
        node_id = clean_node_id(path)
        title = meta.get("title", path)
        concept_type = meta.get("type", "unknown")
        lines.append(f"  {node_id} [label=\"{title}\\n({concept_type})\", style=filled, fillcolor=\"#f5f5f5\"];")
        
    lines.append("")
    
    # Render edges
    for path, meta in concepts.items():
        node_id = clean_node_id(path)
        for rel in meta.get("relations", []) or []:
            target = rel.get("target")
            if target and target in concepts:
                target_id = clean_node_id(target)
                rel_type = rel.get("type", "depends_on")
                ctx = rel.get("rel_context") or {}
                label = rel_type
                if ctx.get("strength"):
                    label += f" ({ctx.get('strength')})"
                lines.append(f"  {node_id} -> {target_id} [label=\"{label}\"];")
                
    lines.append("}")
    return "\n".join(lines) + "\n"


def to_cypher(index):
    lines = []
    concepts = index.get("concepts", {})
    
    # Merge nodes
    for path, meta in concepts.items():
        props = {
            "path": path,
            "title": meta.get("title", ""),
            "type": meta.get("type", ""),
            "description": meta.get("description", ""),
            "status": meta.get("status", "active"),
        }
        props_str = ", ".join(f"{k}: {json.dumps(v)}" for k, v in props.items())
        lines.append(f"MERGE (c:Concept {{path: {json.dumps(path)}}}) ON CREATE SET c = {{{props_str}}} ON MATCH SET c = {{{props_str}}};")
        
    # Merge relationships
    for path, meta in concepts.items():
        for rel in meta.get("relations", []) or []:
            target = rel.get("target")
            if target and target in concepts:
                rel_type = rel.get("type", "depends_on").upper().replace("-", "_").replace(".", "_")
                confidence = rel.get("confidence", "declared")
                ctx = rel.get("rel_context") or {}
                rel_props = {
                    "confidence": confidence,
                    "strength": ctx.get("strength", "hard"),
                    "kind": ctx.get("kind", "api_call"),
                    "note": rel.get("note", "")
                }
                props_str = ", ".join(f"{k}: {json.dumps(v)}" for k, v in rel_props.items())
                lines.append(
                    f"MATCH (src:Concept {{path: {json.dumps(path)}}}), (tgt:Concept {{path: {json.dumps(target)}}}) "
                    f"MERGE (src)-[r:{rel_type} {{{props_str}}}]->(tgt);"
                )
                
    return "\n".join(lines) + "\n"


def to_graphql(index):
    schema = """type Concept {
  path: String!
  title: String!
  type: String!
  description: String
  status: String
  tags: [String!]!
  aliases: [String!]!
  relations: [Relation!]!
  backlinks: [Backlink!]!
}

type Relation {
  type: String!
  target: Concept!
  confidence: String!
  note: String
  strength: String
  kind: String
}

type Backlink {
  source: Concept!
  type: String!
  confidence: String!
}

type Query {
  concept(path: String!): Concept
  concepts(type: String, tag: String): [Concept!]!
}
"""
    return schema


def main(argv=None):
    ap = argparse.ArgumentParser(description="Export the Cairn concept graph.")
    ap.add_argument("--format", choices=["dot", "cypher", "graphql"], required=True, help="Export format")
    ap.add_argument("--root", default=".", help="Root directory of the Cairn bundle")
    ap.add_argument("--output", help="Write export to this file instead of stdout")
    args = ap.parse_args(argv)
    
    index_path = Path(args.root) / "_index.json"
    if not index_path.exists():
        print(f"Error: Index not found at {index_path}. Run 'cairn index' first.", file=sys.stderr)
        return 1
        
    index = json.loads(index_path.read_text(encoding="utf-8"))
    
    if args.format == "dot":
        out = to_dot(index)
    elif args.format == "cypher":
        out = to_cypher(index)
    elif args.format == "graphql":
        out = to_graphql(index)
        
    if args.output:
        out_path = Path(args.output)
        if not out_path.parent.exists():
            print(f"Error: Output directory does not exist: {out_path.parent}", file=sys.stderr)
            return 1
        try:
            out_path.write_text(out, encoding="utf-8")
        except Exception as e:
            print(f"Error writing output: {e}", file=sys.stderr)
            return 1
    else:
        print(out, end="")
        
    return 0


if __name__ == "__main__":
    sys.exit(main())
