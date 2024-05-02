import pytest

from gypsum._utils import _remove_slash_url

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


def test_fib():
    single_slash = _remove_slash_url("https://jkanche.com/")
    assert single_slash == "https://jkanche.com"

    double_slash = _remove_slash_url("https://jkanche.com//")
    assert double_slash == "https://jkanche.com"
