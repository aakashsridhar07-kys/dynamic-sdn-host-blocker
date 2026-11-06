"""Concurrent newline-delimited JSON TCP echo server."""
from __future__ import annotations

import argparse
import logging
import socketserver

from socket_app.protocol import MAX_MESSAGE_BYTES, decode_message, encode_message, make_response

LOG = logging.getLogger("tcp_server")


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True
    request_queue_size = 64


class TCPHandler(socketserver.StreamRequestHandler):
    def handle(self):
        peer = f"{self.client_address[0]}:{self.client_address[1]}"
        LOG.info("TCP client connected: %s", peer)
        while True:
            line = self.rfile.readline(MAX_MESSAGE_BYTES + 2)
            if not line:
                break
            if len(line) > MAX_MESSAGE_BYTES + 1 or not line.endswith(b"\n"):
                LOG.warning("Rejected oversized or unterminated TCP frame from %s", peer)
                break
            try:
                request = decode_message(line[:-1])
                response = make_response(request)
                self.wfile.write(encode_message(response) + b"\n")
                self.wfile.flush()
            except ValueError as exc:
                error = {"status": "error", "error": str(exc)}
                self.wfile.write(encode_message(error) + b"\n")
                self.wfile.flush()
        LOG.info("TCP client disconnected: %s", peer)


def main():
    parser = argparse.ArgumentParser(description="Concurrent TCP JSON echo server")
    parser.add_argument("--host", default="0.0.0.0", help="bind address (default: all interfaces)")
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    with ThreadedTCPServer((args.host, args.port), TCPHandler) as server:
        LOG.info("TCP server listening on %s:%s", args.host, args.port)
        try:
            server.serve_forever(poll_interval=0.5)
        except KeyboardInterrupt:
            LOG.info("TCP server shutting down")


if __name__ == "__main__":
    main()
