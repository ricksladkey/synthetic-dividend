"""Centralized path configuration for the project.

This module provides functions to locate important project directories
regardless of where the code is executed from.
"""

import os
from pathlib import Path


def get_project_root() -> Path:
    """Get the absolute path to the project root directory.

    Returns:
        Path object pointing to the project root (where pyproject.toml lives)
    """
    # This file is at src/paths.py, so go up one level to get project root
    return Path(__file__).parent.parent.resolve()


def get_cache_dir() -> Path:
    """Get the absolute path to the project cache directory.

    This directory is used for caching downloaded price data and other
    temporary files that can be regenerated.

    Returns:
        Path object pointing to <project_root>/cache/
    """
    cache_dir = get_project_root() / "cache"
    cache_dir.mkdir(exist_ok=True)
    return cache_dir


def get_data_dir() -> Path:
    """Get the absolute path to the project data directory.

    This directory contains persistent data like best_sdn.json.

    Returns:
        Path object pointing to <project_root>/data/
    """
    data_dir = get_project_root() / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir


def get_testdata_dir() -> Path:
    """Get the absolute path to the testdata directory.

    This directory contains static CSV files used for testing.

    Returns:
        Path object pointing to <project_root>/testdata/
    """
    return get_project_root() / "testdata"
