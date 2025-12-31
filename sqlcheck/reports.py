from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from xml.etree import ElementTree

from sqlcheck.models import TestResult


def write_plan(result: TestResult, path: Path) -> None:
    payload = {
        "path": str(result.case.path),
        "name": result.case.metadata.name,
        "tags": result.case.metadata.tags,
        "serial": result.case.metadata.serial,
        "timeout": result.case.metadata.timeout,
        "retries": result.case.metadata.retries,
        "statements": [
            {"index": stmt.index, "text": stmt.text, "start": stmt.start, "end": stmt.end}
            for stmt in result.case.sql_parsed.statements
        ],
        "directives": [
            {"name": directive.name, "args": directive.args, "kwargs": directive.kwargs}
            for directive in result.case.directives
        ],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_json(results: list[TestResult], path: Path) -> None:
    payload = []
    for result in results:
        payload.append(
            {
                "path": str(result.case.path),
                "name": result.case.metadata.name,
                "tags": result.case.metadata.tags,
                "serial": result.case.metadata.serial,
                "timeout": result.case.metadata.timeout,
                "retries": result.case.metadata.retries,
                "status": asdict(result.status),
                "output": asdict(result.output),
                "function_results": [asdict(item) for item in result.function_results],
                "success": result.success,
                "statements": [
                    {"index": stmt.index, "text": stmt.text, "start": stmt.start, "end": stmt.end}
                    for stmt in result.case.sql_parsed.statements
                ],
            }
        )
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_junit(results: list[TestResult], path: Path) -> None:
    testsuite = ElementTree.Element("testsuite", name="sqlcheck")
    testsuite.set("tests", str(len(results)))
    testsuite.set("failures", str(sum(1 for result in results if not result.success)))

    for result in results:
        testcase = ElementTree.SubElement(
            testsuite,
            "testcase",
            name=result.case.metadata.name,
            classname=str(result.case.path),
            time=f"{result.status.duration_s:.3f}",
        )
        if not result.success:
            failure = ElementTree.SubElement(testcase, "failure")
            messages = [
                item.message
                for item in result.function_results
                if not item.success and item.message
            ]
            detail = "\n".join(messages)
            failure.text = detail

    tree = ElementTree.ElementTree(testsuite)
    tree.write(path, encoding="utf-8", xml_declaration=True)
