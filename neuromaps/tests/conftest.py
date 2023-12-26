# -*- coding: utf-8 -*-
"""Fixtures for all abagen tests."""

import shutil

import pytest

def pytest_configure(config):
    """Add markers for tests."""
    config.addinivalue_line(
        "markers", "workbench: mark test to run with Connectome Workbench"
    )

def pytest_runtest_setup(item):
    """Skip tests that require workbench if it's not installed."""
    markers = set(mark.name for mark in item.iter_markers())
    if 'workbench' in markers and shutil.which('wb_command') is None:
        pytest.skip('Cannot run without Connectome Workbench')
