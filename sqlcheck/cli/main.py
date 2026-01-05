from __future__ import annotations

import sys

from sqlcheck.cli.app import app


def main(argv: list[str] | None = None) -> None:
    app(args=argv)


if __name__ == "__main__":
    sys.exit(main())
