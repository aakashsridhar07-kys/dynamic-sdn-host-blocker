import socket
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor

from socket_app.protocol import decode_message, encode_message, make_request
from socket_app.tcp_server import TCPHandler, ThreadedTCPServer
from socket_app.udp_server import UDPHandler, ThreadedUDPServer


class SocketTransportTests(unittest.TestCase):
    def setUp(self):
        self.tcp = ThreadedTCPServer(("127.0.0.1", 0), TCPHandler)
        self.udp = ThreadedUDPServer(("127.0.0.1", 0), UDPHandler)
        self.tcp_thread = threading.Thread(target=self.tcp.serve_forever, daemon=True)
        self.udp_thread = threading.Thread(target=self.udp.serve_forever, daemon=True)
        self.tcp_thread.start()
        self.udp_thread.start()

    def tearDown(self):
        self.tcp.shutdown()
        self.udp.shutdown()
        self.tcp.server_close()
        self.udp.server_close()
        self.tcp_thread.join(timeout=2)
        self.udp_thread.join(timeout=2)

    def test_tcp_echo(self):
        request = make_request("tcp test", "tcp-1")
        with socket.create_connection(self.tcp.server_address, timeout=2) as client:
            client.sendall(encode_message(request) + b"\n")
            response = client.makefile("rb").readline(4098)
        self.assertEqual(decode_message(response.rstrip(b"\n"))["message"], "tcp test")

    def test_tcp_handles_multiple_clients_concurrently(self):
        def send_one(index):
            request = make_request(f"client-{index}", str(index))
            with socket.create_connection(self.tcp.server_address, timeout=2) as client:
                client.sendall(encode_message(request) + b"\n")
                line = client.makefile("rb").readline(4098)
            return decode_message(line.rstrip(b"\n"))

        with ThreadPoolExecutor(max_workers=4) as pool:
            responses = list(pool.map(send_one, range(4)))
        self.assertEqual({item["message"] for item in responses},
                         {f"client-{index}" for index in range(4)})

    def test_udp_echo(self):
        request = make_request("udp test", "udp-1")
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
            client.settimeout(2)
            client.sendto(encode_message(request), self.udp.server_address)
            payload, _ = client.recvfrom(4096)
        self.assertEqual(decode_message(payload)["message"], "udp test")


if __name__ == "__main__":
    unittest.main()
