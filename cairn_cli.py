#!/usr/bin/env python3
from pathlib import Path
import argparse
import json
import sys

from tools.auditor.audit import audit, write_report as write_audit_report
from tools.corpus.evaluate import main as corpus_main
from tools.index.index import main as write_index
from tools.merge.merge import main as merge_main
from tools.project_agent.cairnize import run as run_migration
from tools.validate.validate import validate
from tools.query.query import main as query_main
from tools.export.export import main as export_main
from tools.diff.diff import main as diff_main
import importlib.util

def _load_parser():
    path = Path(__file__).resolve().parent / "tools" / "reference-parser" / "parser.py"
    spec = importlib.util.spec_from_file_location("reference_parser_dynamic", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.parse

parse_concept = _load_parser()


def _load_critic():
    path = Path(__file__).resolve().parent / "tools" / "critic-agent" / "critic.py"
    spec = importlib.util.spec_from_file_location("critic_dynamic", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.main

critic_main = _load_critic()


def cmd_validate(args):
    results = validate(Path(args.root))
    print(json.dumps(results, indent=2))
    return 1 if any(not item["valid"] for item in results) else 0


def cmd_index(args):
    index = write_index(Path(args.root))
    print(json.dumps({
        "concepts": len(index.get("concepts", {})),
        "backlinks": len(index.get("backlinks", {})),
        "index": str(Path(args.root) / "_index.json"),
    }, indent=2))
    return 0


def cmd_audit(args):
    root = Path(args.root)
    results = audit(root)
    report = None if args.json_only else write_audit_report(root, results)
    print(json.dumps({"report": str(report) if report else None, "results": results}, indent=2))
    return 0


def cmd_migrate(args):
    run_migration(args)
    return 0


def cmd_parse(args):
    for file in args.files:
        print(json.dumps(parse_concept(file), indent=2, default=str))
    return 0


def cmd_merge(args):
    merge_args = [args.base, args.ours, args.theirs]
    if args.output:
        merge_args.extend(["--output", args.output])
    if args.conflicts_json:
        merge_args.extend(["--conflicts-json", args.conflicts_json])
    return merge_main(merge_args)


def cmd_corpus(args):
    corpus_args = [args.config, "--output", args.output]
    if args.report:
        corpus_args.extend(["--report", args.report])
    corpus_main(corpus_args)
    return 0


def cmd_critic(args):
    return critic_main([args.root])


def cmd_query(args):
    query_args = list(args.filters)
    if args.root:
        query_args.extend(["--root", args.root])
    return query_main(query_args)


def cmd_export(args):
    export_args = ["--format", args.format]
    if args.root:
        export_args.extend(["--root", args.root])
    if args.output:
        export_args.extend(["--output", args.output])
    return export_main(export_args)


def cmd_diff(args):
    diff_args = [args.old_file, args.new_file]
    if args.root:
        diff_args.extend(["--root", args.root])
    return diff_main(diff_args)


def build_parser():
    parser = argparse.ArgumentParser(prog="cairn", description="Validate, index, audit, and migrate Cairn bundles.")
    sub = parser.add_subparsers(dest="command", required=True)

    validate_cmd = sub.add_parser("validate", help="Validate a Cairn bundle.")
    validate_cmd.add_argument("root", nargs="?", default=".")
    validate_cmd.set_defaults(func=cmd_validate)

    index_cmd = sub.add_parser("index", help="Generate _index.json for a Cairn bundle.")
    index_cmd.add_argument("root", nargs="?", default=".")
    index_cmd.set_defaults(func=cmd_index)

    audit_cmd = sub.add_parser("audit", help="Run a per-concept Cairn compliance audit.")
    audit_cmd.add_argument("root", nargs="?", default=".")
    audit_cmd.add_argument("--json-only", action="store_true", help="Do not write a timestamped audit report.")
    audit_cmd.set_defaults(func=cmd_audit)

    migrate_cmd = sub.add_parser("migrate", help="Stage a read-only Cairn migration for a project.")
    migrate_cmd.add_argument("target", help="Project directory to scan")
    migrate_cmd.add_argument("--output", help="Directory for staged concepts and reports")
    migrate_cmd.add_argument("--write-into-target", action="store_true", help="Write cairn-proposed/ and reports/ inside the target project")
    migrate_cmd.set_defaults(func=cmd_migrate)

    parse_cmd = sub.add_parser("parse", help="Parse one or more Cairn concept files.")
    parse_cmd.add_argument("files", nargs="+")
    parse_cmd.set_defaults(func=cmd_parse)

    merge_cmd = sub.add_parser("merge", help="Deterministically merge three Cairn concept versions.")
    merge_cmd.add_argument("base")
    merge_cmd.add_argument("ours")
    merge_cmd.add_argument("theirs")
    merge_cmd.add_argument("--output")
    merge_cmd.add_argument("--conflicts-json")
    merge_cmd.set_defaults(func=cmd_merge)

    corpus_cmd = sub.add_parser("corpus", help="Run migration scanner over a corpus config.")
    corpus_cmd.add_argument("config", help="JSON config with projects[].path")
    corpus_cmd.add_argument("--output", default="corpus-runs")
    corpus_cmd.add_argument("--report")
    corpus_cmd.set_defaults(func=cmd_corpus)

    critic_cmd = sub.add_parser("critic", help="Run the Cairn Critic Agent.")
    critic_cmd.add_argument("root", nargs="?", default=".")
    critic_cmd.set_defaults(func=cmd_critic)

    query_cmd = sub.add_parser("query", help="Query the Cairn index using metadata filters.")
    query_cmd.add_argument("filters", nargs="*")
    query_cmd.add_argument("--root", default=".")
    query_cmd.set_defaults(func=cmd_query)

    export_cmd = sub.add_parser("export", help="Export the Cairn concept graph.")
    export_cmd.add_argument("--format", choices=["dot", "cypher", "graphql"], required=True)
    export_cmd.add_argument("--root", default=".")
    export_cmd.add_argument("--output")
    export_cmd.set_defaults(func=cmd_export)

    diff_cmd = sub.add_parser("diff", help="Semantically diff two Cairn concepts.")
    diff_cmd.add_argument("old_file")
    diff_cmd.add_argument("new_file")
    diff_cmd.add_argument("--root", default=".")
    diff_cmd.set_defaults(func=cmd_diff)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
