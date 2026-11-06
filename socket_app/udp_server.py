"""Concurrent UDP JSON echo server."""
from __future__ import annotations

import argparse
import logging
import socketserver

from socket_app.protocol import MAX_MESSAGE_BYTES, decode_message, encode_message, make_response

LOG = logging.getLogger("udp_server")


class ThreadedUDPServer(socketserver.ThreadingMixIn, socketserver.UDPServer):
    allow_reuse_address = True
    daemon_threads = True


class UDPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        payload, sock = self.request
        try:
            request = decode_message(payload)
            response = make_response(request)
        except ValueError as exc:
            response = {"status": "error", "error": str(exc)}
        try:
            sock.sendto(encode_message(response), self.client_address)
            LOG.info("Handled UDP datagram from %s:%s", *self.client_address)
        except OSError:
            LOG.exception("Failed to reply to UDP client %s", self.client_address)


def main():
    parser = argparse.ArgumentParser(description="Concurrent UDP JSON echo server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=9001)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    with ThreadedUDPServer((args.host, args.port), UDPHandler) as server:
        LOG.info("UDP server listening on %s:%s", args.host, args.port)
        try:
            server.serve_forever(poll_interval=0.5)
        except KeyboardInterrupt:
            LOG.info("UDP server shutting down")


if __name__ == "__main__":
    main()
