from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shlex
import subprocess
import tempfile
import time

from sqlcheck.models import ExecutionOutput, ExecutionStatus


@dataclass(frozen=True)
class ExecutionResult:
    status: ExecutionStatus
    output: ExecutionOutput


class DBConnector:
    name = "base"

    def execute(self, sql: str, timeout: float | None = None) -> ExecutionResult:
        raise NotImplementedError


class CommandDBConnector(DBConnector):
    command_name: str | None = None

    def __init__(
        self,
        engine_args: list[str] | None = None,
        command_template: str | None = None,
    ) -> None:
        self.engine_args = engine_args or []
        self.command_template = command_template

    def execute(self, sql: str, timeout: float | None = None) -> ExecutionResult:
        file_path = None
        start = time.perf_counter()
        try:
            command, stdin_input, file_path = self._prepare_command(sql)
            process = subprocess.run(
                command,
                input=stdin_input,
                text=True,
                capture_output=True,
                timeout=timeout,
            )
            duration = time.perf_counter() - start
            status = ExecutionStatus(
                success=process.returncode == 0,
                returncode=process.returncode,
                duration_s=duration,
            )
            output = ExecutionOutput(stdout=process.stdout, stderr=process.stderr)
            return ExecutionResult(status=status, output=output)
        except subprocess.TimeoutExpired as exc:
            duration = time.perf_counter() - start
            status = ExecutionStatus(success=False, returncode=-1, duration_s=duration)
            output = ExecutionOutput(stdout=exc.stdout or "", stderr=exc.stderr or "Timed out")
            return ExecutionResult(status=status, output=output)
        finally:
            if file_path:
                Path(file_path).unlink(missing_ok=True)

    def _prepare_command(self, sql: str) -> tuple[list[str], str | None, str | None]:
        if not self.command_template:
            if not self.command_name:
                raise RuntimeError("No command_name or command_template configured")
            return [self.command_name, *self.engine_args], sql, None

        template_parts = shlex.split(self.command_template)
        uses_sql = any("{sql}" in part for part in template_parts)
        uses_file = any("{file_path}" in part for part in template_parts)

        file_path = None
        if uses_file:
            with tempfile.NamedTemporaryFile("w", delete=False, suffix=".sql") as handle:
                handle.write(sql)
                file_path = handle.name

        rendered_parts: list[str] = []
        for part in template_parts:
            if part == "{engine_args}":
                rendered_parts.extend(self.engine_args)
                continue
            part = part.replace("{sql}", sql)
            if file_path:
                part = part.replace("{file_path}", file_path)
            rendered_parts.append(part.replace("{engine_args}", " ".join(self.engine_args)))

        stdin_input = None if uses_sql or uses_file else sql
        return rendered_parts, stdin_input, file_path
