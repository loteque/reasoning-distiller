#!/usr/bin/env python3
"""Reasoning Distiller deterministic installer entrypoint.

P1 contract stub. P3 will implement staged install/update/recovery behavior.
This command intentionally performs no network I/O.
"""
from __future__ import annotations

import argparse

INSTALLER_CONTRACT = "reasoning-distiller-installer/1"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Install a verified Reasoning Distiller package into a project workspace.")
    parser.add_argument("--package", required=False)
    parser.add_argument("--manifest", required=False)
    parser.add_argument("--transport-sha256", required=False)
    parser.add_argument("--target", required=False)
    parser.add_argument("--version", action="store_true", help="print installer contract and exit")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.version:
        print(INSTALLER_CONTRACT)
        return 0
    raise SystemExit("P1 contract stub only; deterministic installation is implemented at P3")


if __name__ == "__main__":
    raise SystemExit(main())
