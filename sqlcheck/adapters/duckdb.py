from __future__ import annotations

import subprocess
import time

from sqlcheck.adapters.base import Adapter, ExecutionResult
from sqlcheck.models import ExecutionOutput, ExecutionStatus


class DuckDBAdapter(Adapter):
    name = "duckdb"

    def __init__(self, database: str | None = None) -> None:
        self.database = database or ":memory:"

    def execute(self, sql: str, timeout: float | None = None) -> ExecutionResult:
        start = time.perf_counter()
        try:
            process = subprocess.run(
                ["duckdb", self.database],
                input=sql,
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
