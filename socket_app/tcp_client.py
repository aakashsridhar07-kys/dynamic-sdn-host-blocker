"""TCP JSON client for the Mininet and VirtualBox lab."""
from __future__ import annotations

import argparse
import socket

from socket_app.protocol import decode_message, encode_message, make_request


def main():
    parser = argparse.ArgumentParser(description="Send one JSON echo request over TCP")
    parser.add_argument("--host", default="10.20.0.10")
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument("--message", default="Hello from TCP client")
    parser.add_argument("--timeout", type=float, default=5.0)
    args = parser.parse_args()
    request = make_request(args.message)
    with socket.create_connection((args.host, args.port), timeout=args.timeout) as sock:
        sock.settimeout(args.timeout)
        sock.sendall(encode_message(request) + b"\n")
        stream = sock.makefile("rb")
        line = stream.readline(4098)
        if not line or not line.endswith(b"\n"):
            raise RuntimeError("server closed connection or returned an invalid frame")
        print(decode_message(line[:-1]))


if __name__ == "__main__":
    main()
