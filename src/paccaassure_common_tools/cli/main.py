from __future__ import annotations

import argparse
import json
from pathlib import Path

from paccaassure_common_tools.certification import run_certification
from paccaassure_common_tools.invocation import InvocationManager, build_workspace, default_policy
from paccaassure_common_tools.registry import build_default_registry


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pacca-tools")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list-tools")

    manifest = subparsers.add_parser("export-manifest")
    manifest.add_argument("--output", required=True)

    invoke = subparsers.add_parser("invoke")
    invoke.add_argument("--tool-key", required=True)
    invoke.add_argument("--version", default="0.1.0")
    invoke.add_argument("--payload", required=True, help="JSON payload string or @path")
    invoke.add_argument("--workspace", required=True)
    invoke.add_argument("--idempotency-key", required=True)

    certify = subparsers.add_parser("certify")
    certify.add_argument("--fixtures-root", required=True)
    certify.add_argument("--workspace", required=True)
    certify.add_argument("--output", required=True)
    return parser


def load_payload(raw: str) -> dict[str, object]:
    if raw.startswith("@"):
        return json.loads(Path(raw[1:]).read_text(encoding="utf-8"))
    return json.loads(raw)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    registry = build_default_registry()

    if args.command == "list-tools":
        print(
            json.dumps(
                [item.identity.model_dump(mode="json") for item in registry.list_tools()], indent=2
            )
        )
        return 0

    if args.command == "export-manifest":
        Path(args.output).write_text(
            registry.export_manifest().model_dump_json(indent=2),
            encoding="utf-8",
        )
        return 0

    if args.command == "invoke":
        workspace = build_workspace(Path(args.workspace))
        manager = InvocationManager(registry)
        result = manager.invoke(
            tool_key=args.tool_key,
            version=args.version,
            payload=load_payload(args.payload),
            policy=default_policy(),
            workspace=workspace,
            idempotency_key=args.idempotency_key,
        )
        print(result.model_dump_json(indent=2))
        return 0

    if args.command == "certify":
        report = run_certification(
            registry,
            fixtures_root=Path(args.fixtures_root),
            workspace_root=Path(args.workspace),
            commands=["pacca-tools certify"],
        )
        Path(args.output).write_text(report.model_dump_json(indent=2), encoding="utf-8")
        print(report.model_dump_json(indent=2))
        return 0

    parser.error("Unsupported command")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
