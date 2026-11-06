"""UDP JSON client for the Mininet and VirtualBox lab."""
from __future__ import annotations

import argparse
import socket

from socket_app.protocol import decode_message, encode_message, make_request


def main():
    parser = argparse.ArgumentParser(description="Send one JSON echo datagram over UDP")
    parser.add_argument("--host", default="10.20.0.10")
    parser.add_argument("--port", type=int, default=9001)
    parser.add_argument("--message", default="Hello from UDP client")
    parser.add_argument("--timeout", type=float, default=3.0)
    args = parser.parse_args()
    request = make_request(args.message)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(args.timeout)
        sock.sendto(encode_message(request), (args.host, args.port))
        payload, _peer = sock.recvfrom(4096)
    print(decode_message(payload))


if __name__ == "__main__":
    main()
