import os
import time
from typing import Optional, Union

import requests
from filelock import FileLock

from ._github import github_access_token
from ._utils import _is_interactive, _remove_slash_url
from .cache_directory import cache_directory
from .config import REQUESTS_MOD
from .rest_url import rest_url

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"

TOKEN_CACHE = {}


def _token_cache_path(cache_dir):
    return os.path.join(cache_dir, "credentials", "token.txt")


def access_token(
    full: bool = False,
    request: bool = True,
    cache_dir: Optional[str] = cache_directory(),
    token_expiration_limit: int = 10,
) -> Optional[Union[str, dict]]:
    """Get GitHub access token for authentication to the gypsum API's.

    Example:

        .. code-block:: python

            token = access_token()

    Args:
        full:
            Whether to return the full token details.
            Defaults to False, only ``token`` is returned.

        request:
            Whether to request a new token if no token is found or the
            current token is expired. Defaults to True.

        cache_dir:
            Path to the cache directory to store tokens.
            Can be set to `None`, indicating token is not cached to disk.

        token_expiration_limit:
            Integer specifying the number of seconds until the token expires.

    Returns:
        If `full=False` A string specifying the GitHub token to
        access gypsum's resources.

        If `full=True` retuns a dicionary containing the full token details.
    """
    global TOKEN_CACHE

    def _token_func(x):
        return x["token"] if not full else x

    in_memory = TOKEN_CACHE.get("auth_info", None)
    if in_memory is not None:
        if in_memory["expires"] > time.time() + token_expiration_limit:
            return _token_func(in_memory)
        else:
            TOKEN_CACHE["auth_info"] = None

    if cache_dir is not None:
        cache_path = _token_cache_path(cache_dir)

        if os.path.exists(cache_path):
            _lock = FileLock(cache_path + ".LOCK")
            with _lock:
                with open(cache_path, "r") as file:
                    dump = file.read().splitlines()

            if len(dump) > 0:
                exp = float(dump[2])
                if exp > time.time() + token_expiration_limit:
                    info = {"token": dump[0], "name": dump[1], "expires": exp}
                    TOKEN_CACHE["auth_info"] = info
                    return _token_func(info)
            else:
                os.unlink(cache_path)

    if request:
        payload = set_access_token(cache_dir=cache_dir)
        return _token_func(payload) if payload else None
    else:
        return None


TOKEN_AUTO = "auto"


def set_access_token(
    token: str = TOKEN_AUTO,
    app_url: str = rest_url(),
    app_key: Optional[str] = None,
    app_secret: Optional[str] = None,
    github_url: str = "https://api.github.com",
    user_agent: Optional[str] = None,
    cache_dir: Optional[str] = cache_directory(),
) -> dict:
    """Set GitHub access token for authentication to the gypsum API's.

    Args:
        token:
            A String containing Github's personal access token.

        app_url:
            URL to the gypsum REST API.

        app_key:
            Key to the GitHub oauth app.

        app_secret:
            Secret to the GitHub oauth app.

        github_url:
            URL to GitHub's API.

        user_agent:
            Specify the user agent for queries to various endpoints.

        cache_dir:
            Path to the cache directory to store tokens.
            Defaults to None, indicating token is not cached to disk.

    Returns:
        Dictionary containing the following keys:
        - ``token``, a string containing the token.
        - ``name``, the name of the GitHub user authenticated by the token.
        - ``expires``, the Unix time at which the token expires.
    """
    global TOKEN_CACHE

    cache_path = None
    if cache_dir is not None:
        cache_path = _token_cache_path(cache_dir)

    if token is None:
        TOKEN_CACHE["auth_info"] = None
        if cache_path is not None:
            os.unlink(cache_path)

        return

    if token is TOKEN_AUTO:
        if not _is_interactive():
            raise Exception(
                "Running in non-interactive mode. Set the token manually using `set_access_token`."
            )

        if not app_key or not app_secret:
            _url = f"{_remove_slash_url(app_url)}/credentials/github-app"
            headers = {}
            if user_agent:
                headers["User-Agent"] = user_agent

            r = requests.get(_url, headers=headers, verify=REQUESTS_MOD["verify"])
            try:
                r.raise_for_status()
            except Exception as e:
                raise Exception(
                    f"Failed to get access credentials from gypsum, {r.status_code} and reason: {r.text}"
                ) from e

            _info = r.json()
            app_key = _info["id"]
            app_secret = _info["secret"]

        token = github_access_token(
            client_id=app_key,
            client_secret=app_secret,
            authorization_url="https://github.com/login/oauth/authorize",
            token_url="https://github.com/login/oauth/access_token",
        )

    if token is None:
        raise ValueError("'token' cannot be 'None'.")

    headers = {}
    if user_agent:
        headers["User-Agent"] = user_agent

    headers["Authorization"] = f"Bearer {token}"

    token_req = requests.get(
        f"{_remove_slash_url(github_url)}/user",
        headers=headers,
        verify=REQUESTS_MOD["verify"],
    )
    try:
        token_req.raise_for_status()
    except Exception as e:
        raise Exception(
            f"Failed to access token from GitHub, {token_req.status_code} and reason: {token_req.text}"
        ) from e

    token_resp = token_req.json()
    name = token_resp["login"]
    expires_header = token_req.headers.get("github-authentication-token-expiration")

    expiry = float("inf")
    if expires_header is not None:
        expiry = float(expires_header.split(" ")[0])

    if cache_dir is not None:
        cache_path = _token_cache_path(cache_dir)
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)

        _lock = FileLock(cache_path + ".LOCK")
        with _lock:
            with open(cache_path, "w") as file:
                file.write("\n".join([token, name, str(expiry)]))

        os.chmod(
            cache_path, 0o600
        )  # prevent anyone else from reading this on shared file systems.

    vals = {"token": token, "name": name, "expires": expiry}
    TOKEN_CACHE["auth_info"] = vals
    return vals
