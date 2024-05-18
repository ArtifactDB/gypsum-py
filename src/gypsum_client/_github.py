import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests

from .config import REQUESTS_MOD

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"

AUTH_CODE = None


def github_access_token(client_id, client_secret, authorization_url, token_url):
    """Get access token from GitHub.

    Users should look at :pu:func:`~.auth.access_token` function.

    This process temporarily spins up a server similar to capture the redirction url and
    extract the access token similar to how httr's `oauth_flow_auth_code` method.
    This allows us to programmatically capture access tokens from the url without the user
    having to manually input the code.

    Follows authentication flow described here -
    https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-user-access-token-for-a-github-app.
    """

    class AuthorizationHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            global AUTH_CODE
            if self.path.startswith("/?code"):
                AUTH_CODE = self.path.split("/?code=")[1]

                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(
                    b"<h2>Authorization Code Received. Close this tab and go back to the python session.</h2>"
                )

                raise SystemExit

    def start_temp_server():
        server = HTTPServer(("localhost", 1410), AuthorizationHandler)
        server.serve_forever()

    _auth_url = (
        f"{authorization_url}?client_id={client_id}&redirect_url=http://localhost:1410"
    )

    server_thread = threading.Thread(target=start_temp_server)
    server_thread.start()
    webbrowser.open(_auth_url)
    server_thread.join()

    headers = {"accept": "application/json"}
    parameters = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": AUTH_CODE,
    }
    token_req = requests.post(
        token_url, headers=headers, json=parameters, verify=REQUESTS_MOD["verify"]
    )

    try:
        token_req.raise_for_status()
    except Exception as e:
        raise Exception(
            f"Failed to access token, {token_req.status_code} and reason: {token_req.text}"
        ) from e

    token = token_req.json()["access_token"]

    return token
