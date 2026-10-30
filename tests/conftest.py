"""Requirement markers.

Tag a test with the requirement(s) it verifies:

    @pytest.mark.req("F3")
    @pytest.mark.req("F5", "F16")

Unknown IDs fail collection. Outcomes are written to reports/req_results.json, which
scripts/traceability.py turns into docs/TRACEABILITY.md.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "reports" / "req_results.json"

_reqs_by_node: dict[str, list[str]] = {}
_outcomes: dict[str, str] = {}


def _known_ids() -> set[str]:
    spec = yaml.safe_load((ROOT / "requirements.yaml").read_text())
    return {r["id"] for r in spec["requirements"]}


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "req(*ids): requirement IDs this test verifies")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    known = _known_ids()
    unknown: list[str] = []
    for item in items:
        ids = [i for m in item.iter_markers("req") for i in m.args]
        if not ids:
            continue
        unknown += [f"{item.nodeid}: {i}" for i in ids if i not in known]
        _reqs_by_node[item.nodeid] = sorted(set(ids))
    if unknown:
        raise pytest.UsageError("unknown requirement IDs:\n  " + "\n  ".join(unknown))


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    if report.nodeid not in _reqs_by_node:
        return
    if hasattr(report, "wasxfail"):
        _outcomes[report.nodeid] = "xfail"
    elif report.failed:
        _outcomes[report.nodeid] = "failed"
    elif report.skipped:
        _outcomes.setdefault(report.nodeid, "skipped")
    elif report.when == "call":
        _outcomes.setdefault(report.nodeid, "passed")


def pytest_sessionfinish(session: pytest.Session) -> None:
    RESULTS.parent.mkdir(exist_ok=True)
    data = {
        node: {"reqs": reqs, "outcome": _outcomes.get(node, "not run")}
        for node, reqs in sorted(_reqs_by_node.items())
    }
    RESULTS.write_text(json.dumps(data, indent=2) + "\n")
