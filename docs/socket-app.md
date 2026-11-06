# TCP and UDP socket applications

The socket demo uses a small JSON echo protocol and only Python's standard
library. TCP messages are UTF-8 JSON objects terminated by a newline. UDP
messages are one UTF-8 JSON object per datagram. Both transports use ports
9000 (TCP) and 9001 (UDP) by default.

## Install and unit tests

From the repository root:

```bash
source .venv/bin/activate
python -m pip install -e .
python -m unittest tests.test_socket_protocol -v
```

## Run inside Mininet

Start the OS-Ken controller and Mininet topology as described in
[controller.md](controller.md). At the `mininet>` prompt, start both servers
in the background on h3:

```text
h3 python3 -m socket_app.tcp_server --host 10.20.0.10 --port 9000 > /tmp/tcp-server.log 2>&1 &
h3 python3 -m socket_app.udp_server --host 10.20.0.10 --port 9001 > /tmp/udp-server.log 2>&1 &
```

Run TCP and UDP clients from both client hosts:

```text
h1 python3 -m socket_app.tcp_client --host 10.20.0.10 --message "hello over TCP"
h2 python3 -m socket_app.tcp_client --host 10.20.0.10 --message "second TCP client"
h1 python3 -m socket_app.udp_client --host 10.20.0.10 --message "hello over UDP"
h2 python3 -m socket_app.udp_client --host 10.20.0.10 --message "second UDP client"
```

Successful clients print a JSON response with `"status": "ok"` and the
message echoed by h3. To inspect server logs:

```text
h3 cat /tmp/tcp-server.log
h3 cat /tmp/udp-server.log
```

Stop the servers from the Mininet CLI:

```text
h3 pkill -f 'socket_app.tcp_server'
h3 pkill -f 'socket_app.udp_server'
```

If Python cannot import `socket_app` from a Mininet host, start Mininet from
the repository root and check that the repository directory is the current
working directory inherited by Mininet hosts.

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

The TCP server handles concurrent client connections with a thread per
connection. The UDP server dispatches datagrams using a thread per request.
Both servers log client activity and stop cleanly when interrupted.

This milestone implements socket communication only. Dynamic controller
integration, traffic classification, and performance benchmarking are
separate follow-on tasks and are not claimed as complete here.
