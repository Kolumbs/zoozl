"""Zoozl tests.

`load_tests` function is used by unittest to load all tests from package.

`load_configuration` function is used to setup CONFIGURATION dictionary
"""

import os
import tomllib
from types import MappingProxyType


def load_configuration(config_file: str = "tests/data/conf.toml"):
    """Load server configuration."""
    with open(config_file, "rb") as file:
        return MappingProxyType(tomllib.load(file))


def load_tests(loader, standard_tests, pattern):
    """Load all tests automatically from tests module.

    Recurses into tests directory and assumes all .py extensions to be test
    files, except ones that start with _
    """
    pattern = "[!_]*.py"
    this_dir = os.path.dirname(__file__)
    package_tests = loader.discover(start_dir=this_dir, pattern=pattern)
    standard_tests.addTests(package_tests)
    return standard_tests
