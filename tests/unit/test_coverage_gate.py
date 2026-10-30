from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.mark.req("NF5")
def test_coverage_gate_is_70_percent_on_the_backend_package() -> None:
    config = tomllib.loads((ROOT / "pyproject.toml").read_text())
    addopts = config["tool"]["pytest"]["ini_options"]["addopts"]
    assert "--cov=nerdhealth" in addopts
    assert "--cov-fail-under=70" in addopts
