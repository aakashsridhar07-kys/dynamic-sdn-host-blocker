import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from dynamic_sdn_blocker.controller_client import ControllerAPIError, ControllerClient


class Handler(BaseHTTPRequestHandler):
    calls = []

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length))
        self.calls.append((self.command, self.path, payload))
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"blocked"}')

    def do_DELETE(self):
        self.calls.append((self.command, self.path, None))
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"unblocked"}')

    def log_message(self, *_args):
        pass


class ControllerClientTests(unittest.TestCase):
    def setUp(self):
        Handler.calls = []
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.client = ControllerClient(f"http://127.0.0.1:{self.server.server_port}")

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def test_health_and_block_request(self):
        self.assertEqual(self.client.health()["status"], "ok")
        self.assertEqual(self.client.block("10.20.0.1", 120)["status"], "blocked")
        self.assertEqual(Handler.calls[-1], (
            "POST", "/v1/blocks", {"ip": "10.20.0.1", "block_seconds": 120}
        ))

    def test_unblock_request(self):
        self.assertEqual(self.client.unblock("10.20.0.1")["status"], "unblocked")
        self.assertEqual(Handler.calls[-1], ("DELETE", "/v1/blocks/10.20.0.1", None))

    def test_connection_failure_is_reported(self):
        client = ControllerClient("http://127.0.0.1:1", timeout=0.1)
        with self.assertRaises(ControllerAPIError):
            client.health()


if __name__ == "__main__":
    unittest.main()
