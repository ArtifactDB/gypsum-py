import os
import tempfile
from datetime import datetime, timedelta

import pytest
from gypsum_client.auth import access_token, set_access_token

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


@pytest.mark.skipif(
    "gh_token" not in os.environ, reason="GitHub token not in environment"
)
def test_setting_the_token_works_as_expected():
    gh_token = os.environ.get("gh_token", None)
    if gh_token is None:
        raise ValueError("GitHub token not in environment")

    out = set_access_token(gh_token, cache_dir=None)
    assert out["token"] == gh_token
    assert access_token(cache_dir=None) == gh_token

    # Works when we cache it to disk.
    with tempfile.TemporaryDirectory() as cache:
        out = set_access_token(gh_token, cache_dir=cache)
        assert out["token"] == gh_token
        assert access_token(cache_dir=cache) == gh_token

        tokpath = os.path.join(cache, "credentials", "token.txt")
        with open(tokpath, "r") as f:
            assert f.readline().strip() == gh_token

        # Unsetting it works as expected.
        out = set_access_token(None, cache_dir=None)
        # Assuming gypsum.token_cache.auth_info should be None
        assert getattr(set_access_token, "auth_info", None) is None
        assert os.path.exists(tokpath)

        out = set_access_token(None, cache_dir=cache)
        assert getattr(set_access_token, "auth_info", None) is None
        assert not os.path.exists(tokpath)


@pytest.mark.skipif(
    "gh_token" not in os.environ, reason="GitHub token not in environment"
)
def test_access_token_retrieval_works_as_expected():
    gh_token = os.environ.get("gh_token", None)
    if gh_token is None:
        raise ValueError("GitHub token not in environment")

    set_access_token(None, cache_dir=None)  # wipe out in-memory cache.

    with tempfile.TemporaryDirectory() as cache:
        tokpath = os.path.join(cache, "credentials", "token.txt")
        os.makedirs(os.path.dirname(tokpath), exist_ok=True)
        with open(tokpath, "w") as f:
            f.write(
                f"foobar\nurmom\n{(datetime.now() + timedelta(seconds=10000)).timestamp()}\n"
            )

        info = access_token(full=True, request=False, cache_dir=cache)
        assert info["token"] == "foobar"
        assert info["name"] == "urmom"
        assert isinstance(info["expires"], float)

        # Works from cache.
        info = access_token(full=True, request=False, cache_dir=None)
        assert info["token"] == "foobar"
        assert info["name"] == "urmom"
        assert isinstance(info["expires"], float)

        # Falls through to request.
        set_access_token(None, cache_dir=None)  # wipe out in-memory cache.
        os.unlink(tokpath)
        info = access_token(full=True, request=False, cache_dir=cache)
        assert info is None


@pytest.mark.skipif(
    "gh_token" not in os.environ, reason="GitHub token not in environment"
)
def test_access_token_expiry_works_as_expected():
    gh_token = os.environ.get("gh_token", None)
    if gh_token is None:
        raise ValueError("GitHub token not in environment")
    set_access_token(None, cache_dir=None)  # wipe out in-memory cache.

    with tempfile.TemporaryDirectory() as cache:
        tokpath = os.path.join(cache, "credentials", "token.txt")
        os.makedirs(os.path.dirname(tokpath), exist_ok=True)
        with open(tokpath, "w") as f:
            f.write(
                "foobar\nurmom\n{}\n".format(
                    (datetime.now() - timedelta(seconds=10000)).timestamp()
                )
            )

        info = access_token(full=True, request=False, cache_dir=cache)
        assert info is None

        # Works in memory as well.
        info = access_token(full=True, request=False, cache_dir=None)
        assert info is None
