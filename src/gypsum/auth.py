import os
import time
from typing import Optional

from filelock import FileLock
from requests import get

from ._github import github_auth_token
from ._utils import _cache_directory, _remove_slash_url, _rest_url

TOKEN_CACHE = {}


def _token_cache_path(cache_dir):
    return os.path.join(cache_dir, "credentials", "token.txt")


def access_token(
    full: bool = False, request: bool = True, cache_dir: Optional[str] = None
):
    """Get GitHub access tokens for authentication to the gypsum API's.

    Args:
        full:
            Whether to return the full token details.
            Defaults to False.

        request:
            Whether to request a new token if no token is found or the
            current token is expired. Defaults to True.

        cache_dir:
            Path to the cache directory to store tokens.
            Defaults to None, indicating token is not cached to disk.

    Returns:
        The GitHub token to access gypsum's resources.
    """
    global TOKEN_CACHE
    expiry_leeway = 10  # number of seconds until use of the token.

    def _token_func(x):
        return x["token"] if not full else x

    cache_dir = _cache_directory(cache_dir)

    in_memory = TOKEN_CACHE.get("auth_info")
    if in_memory is not None:
        if in_memory["expires"] > time.time() + expiry_leeway:
            return _token_func(in_memory)
        else:
            TOKEN_CACHE["auth_info"] = None

    if cache_dir:
        cache_path = _token_cache_path(cache_dir)
        if os.path.exists(cache_path):
            _lock = FileLock(cache_path)
            with _lock:
                with open(cache_path, "r") as file:
                    dump = file.read().splitlines()

            exp = float(dump[2])
            if exp > time.time() + expiry_leeway:
                info = {"token": dump[0], "name": dump[1], "expires": exp}
                TOKEN_CACHE["auth_info"] = info
                return _token_func(info)
            else:
                os.unlink(cache_path)

    if request:
        payload = set_access_token(cache=cache_dir)
        return _token_func(payload) if payload else None
    else:
        return None


def set_access_token(
    token: Optional[str] = None,
    app_url: Optional[str] = _rest_url(),
    app_key: Optional[str] = None,
    app_secret: Optional[str] = None,
    github_url: str = "https://api.github.com",
    user_agent: Optional[str] = None,
    cache_dir: Optional[str] = None,
):
    """Set GitHub access tokens for authentication to the gypsum API's.

    Args:
        token:
            A String containing Github's personal access token.
            Defaults to None.

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
        The GitHub token to access gypsum's resources.
    """
    global TOKEN_CACHE

    cache_dir = _cache_directory(cache_dir)

    if not token:
        if not app_key or not app_secret:
            _url = f"{_remove_slash_url(app_url)}/credentials/github-app"
            headers = {}
            if user_agent:
                headers["User-Agent"] = user_agent

            r = get(_url, headers=headers)
            r.raise_for_status()

            _info = r.json()
            print(_info)
            app_key = _info["id"]
            app_secret = _info["secret"]

        token = github_auth_token(
            client_id=app_key,
            client_secret=app_secret,
            authorization_url="https://github.com/login/oauth/authorize",
            token_url="https://github.com/login/oauth/access_token",
        )

    headers = {}
    if user_agent:
        headers["User-Agent"] = user_agent

    headers["Authorizaton"] = f"Bearer {token}"

    req = get(f"{_remove_slash_url(github_url)}/user", headers=headers)
    req.raise_for_status()

    res = req.json()

    name = res["login"]
    expires_header = req.headers.get("github-authentication-token-expiration")
    expiry = float(expires_header.split()[0]) if expires_header else float("inf")

    if not cache_dir:
        cache_path = _token_cache_path(cache_dir)
        os.makedirs(cache_path, exist_ok=True)

        _lock = FileLock(cache_path)
        with _lock:
            with open(cache_path, "w") as file:
                file.write("\n".join([token, name, str(expiry)]))

        os.chmod(
            cache_path, 0o600
        )  # prevent anyone else from reading this on shared file systems.

    vals = {"token": token, "name": name, "expires": expiry}
    TOKEN_CACHE["auth_info"] = vals
    return vals
