"""Backend test fixtures"""

import os
import sys
import asyncio
from pathlib import Path
from typing import Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Override config paths before importing anything else
import config as config_module

# Use temp directories for testing
_test_dir = Path(__file__).parent / "_test_data"
_test_global_dir = _test_dir / "global"
_test_project_dir = _test_dir / "project"


def _setup_test_dirs():
    """Create test directory structure."""
    _test_global_dir.mkdir(parents=True, exist_ok=True)
    _test_project_dir.mkdir(parents=True, exist_ok=True)
    (_test_global_dir / "skills").mkdir(exist_ok=True)
    (_test_project_dir / "skills").mkdir(exist_ok=True)
    (_test_project_dir / "stats").mkdir(exist_ok=True)
    (_test_project_dir / "conversations").mkdir(exist_ok=True)


def _cleanup_test_dirs():
    """Remove test directory structure."""
    import shutil
    if _test_dir.exists():
        shutil.rmtree(_test_dir)


# Monkey-patch config paths for testing
_original_global = config_module.get_global_config_path
_original_project = config_module.get_project_config_path

config_module.get_global_config_path = lambda: _test_global_dir
config_module.get_project_config_path = lambda: _test_project_dir
config_module.get_config_path = lambda scope: _test_global_dir if scope == "global" else _test_project_dir
config_module.get_stats_dir = lambda: _test_project_dir / "stats"
config_module.get_conversations_dir = lambda: _test_project_dir / "conversations"


@pytest.fixture(scope="session", autouse=True)
def setup_dirs():
    _setup_test_dirs()
    yield
    _cleanup_test_dirs()


@pytest.fixture(autouse=True)
def clean_test_data():
    """Clean test data between tests."""
    yield
    # Clean up skills files
    for scope_dir in [_test_global_dir / "skills", _test_project_dir / "skills"]:
        if scope_dir.exists():
            for f in scope_dir.iterdir():
                if f.suffix == ".md":
                    f.unlink()
    # Clean up settings
    for d in [_test_global_dir, _test_project_dir]:
        settings = d / "settings.json"
        if settings.exists():
            settings.unlink()
    # Clean stats
    stats_dir = _test_project_dir / "stats"
    if stats_dir.exists():
        for f in stats_dir.iterdir():
            f.unlink()
    # Clean conversations
    conv_dir = _test_project_dir / "conversations"
    if conv_dir.exists():
        for f in conv_dir.iterdir():
            f.unlink()


@pytest_asyncio.fixture
async def client():
    """Async HTTP test client."""
    from main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as c:
        yield c
