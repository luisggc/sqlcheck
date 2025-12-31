from __future__ import annotations

import typer

from sqlcheck.cli.commands.parse import parse
from sqlcheck.cli.commands.plan import plan
from sqlcheck.cli.commands.run import run

app = typer.Typer(help="Run SQL test files.", add_completion=False)

app.command()(run)
app.command()(parse)
app.command()(plan)
