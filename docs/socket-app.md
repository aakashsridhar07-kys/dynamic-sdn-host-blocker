# TCP and UDP socket applications

The socket demo uses a small JSON echo protocol and only Python's standard
library. TCP messages are UTF-8 JSON objects terminated by a newline. UDP
messages are one UTF-8 JSON object per datagram. Both transports use ports
9000 (TCP) and 9001 (UDP) by default.

## Install and tests

From the repository root:

```bash
source .venv/bin/activate
python -m pip install -e .
PYTHONPATH=. python -m unittest tests.test_socket_protocol -v
```

## Run inside Mininet

Start the controller and topology as described in [controller.md](controller.md).
At the `mininet>` prompt, launch the TCP server on h3:

```text
h3 python3 -m socket_app.tcp_server --host 10.20.0.10 --port 9000
```

Open another terminal or use a second Mininet CLI command to start the UDP
server:

```text
h3 python3 -m socket_app.udp_server --host 10.20.0.10 --port 9001
```

Then run clients from h1 and h2:

```text
h1 python3 -m socket_app.tcp_client --host 10.20.0.10 --message "hello over TCP"
h2 python3 -m socket_app.tcp_client --host 10.20.0.10 --message "second TCP client"
h1 python3 -m socket_app.udp_client --host 10.20.0.10 --message "hello over UDP"
h2 python3 -m socket_app.udp_client --host 10.20.0.10 --message "second UDP client"
```

The TCP server handles concurrent client connections with a thread per
connection. The UDP server dispatches datagrams using a thread per request.
Both servers log client activity and stop with Ctrl+C in their Mininet host
terminal. For interactive server processes, start them in separate terminals
using Mininet's `xterm h3` if X11 is available, or background them with
`h3 python3 -m socket_app.tcp_server ... &` and stop them with
`h3 pkill -f socket_app.tcp_server` from the Mininet CLI.

## Message format

Request:

```json
{"id":"1","type":"echo","message":"hello"}
```

Response:

```json
{"id":"1","status":"ok","message":"hello"}
```

The protocol rejects malformed JSON, non-object messages, empty echo
messages, and payloads larger than 4096 bytes. TCP uses newline framing to
preserve message boundaries; UDP preserves datagram boundaries. UDP is
connectionless and does not guarantee delivery, ordering, or retransmission.

This milestone implements socket communication only. Dynamic controller
integration, traffic classification, and performance benchmarking are
separate follow-on tasks and are not claimed as complete here.
