import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests
from requests_oauthlib import OAuth2Session

AUTH_CODE = None


def github_auth_token(client_id, client_secret, authorization_url, token_url):
    class AuthorizationHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            global AUTH_CODE
            if self.path.startswith("/?code"):
                AUTH_CODE = self.path.split("/?code=")[1]

                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(
                    b"<h2>Authorization Code Received, Close this tab and go back to the session</h2>"
                )

                raise SystemExit

    def start_temp_server():
        server = HTTPServer(("localhost", 1410), AuthorizationHandler)
        server.serve_forever()

    github = OAuth2Session(client_id)
    _auth_url, _ = github.authorization_url(authorization_url)

    server_thread = threading.Thread(target=start_temp_server)
    server_thread.start()
    webbrowser.open(_auth_url)
    server_thread.join()

    headers = {"accept": "*/*"}
    parameters = {
        "client_id": client_id,
        "client_secret": client_secret,
        "access_code": AUTH_CODE,
    }
    response = requests.get(token_url, headers=headers, params=parameters)
    print(response.text)
    token = response.text

    print(token)

    # token = github.fetch_token(
    #     token_url, code=AUTH_CODE, client_secret=client_secret
    # )

    return token
