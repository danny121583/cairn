#!/usr/bin/env python3
from pathlib import Path
import sys
import yaml


def split_frontmatter(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    meta = yaml.safe_load(text[4:end]) or {}
    return meta, text[end + 5 :]


def parse(path):
    meta, body = split_frontmatter(Path(path).read_text(encoding="utf-8"))
    return {
        "path": str(path),
        "type": meta.get("type"),
        "title": meta.get("title"),
        "aliases": meta.get("aliases", []),
        "relations": meta.get("relations", []),
        "frontmatter": meta,
        "body": body,
    }


if __name__ == "__main__":
    for file in sys.argv[1:]:
        concept = parse(file)
        print(yaml.safe_dump(concept, sort_keys=False))
