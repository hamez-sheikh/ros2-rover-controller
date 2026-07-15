"""Shared test fixtures. FIXTURES points at the repo's checked-in projects."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = REPO_ROOT / "fixtures"
RULEPACKS = REPO_ROOT / "rulepacks"


@pytest.fixture
def good_copy(tmp_path: Path) -> Path:
    """A mutable copy of the 'good' fixture, with the rulepack alongside so
    rulepack discovery works from the temp directory."""
    dest = tmp_path / "good"
    shutil.copytree(FIXTURES / "good", dest)
    shutil.copytree(RULEPACKS, tmp_path / "rulepacks")
    return dest
