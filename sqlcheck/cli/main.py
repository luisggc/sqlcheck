from __future__ import annotations

import sys

import typer

from sqlcheck.cli.app import app


def main(argv: list[str] | None = None) -> int:
    try:
        app(standalone_mode=False, args=argv)
    except typer.Exit as exc:
        return exc.exit_code
    return 0


if __name__ == "__main__":
    sys.exit(main())
