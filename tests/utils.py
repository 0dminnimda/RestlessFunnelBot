"""
Things that simplify the testing process and help with it
"""

import pytest


def setup():
    pass


def do_test(file: str) -> None:
    pytest.main([
        file, "-vv", "-W", "ignore::pytest.PytestAssertRewriteWarning"])
