"""
conftest.py — pytest-playwright configuration for OpenClaw Academy tests.
"""

import pytest


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    """Launch Chromium headless with sandbox flags for macOS."""
    return {
        **browser_type_launch_args,
        "headless": True,
        "args": ["--no-sandbox", "--disable-dev-shm-usage"],
    }
