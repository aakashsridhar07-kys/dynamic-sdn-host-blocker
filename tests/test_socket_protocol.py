import unittest

from socket_app.protocol import (
    MAX_MESSAGE_BYTES, decode_message, encode_message, make_request, make_response,
)


class SocketProtocolTests(unittest.TestCase):
    def test_json_round_trip(self):
        message = make_request("hello", "abc")
        self.assertEqual(decode_message(encode_message(message)), message)

    def test_echo_response(self):
        response = make_response(make_request("network test", "7"))
        self.assertEqual(response, {"id": "7", "status": "ok", "message": "network test"})

    def test_rejects_non_object_json(self):
        with self.assertRaises(ValueError):
            decode_message(b'["not", "an", "object"]')

    def test_rejects_invalid_json(self):
        with self.assertRaises(ValueError):
            decode_message(b"{broken")

    def test_rejects_oversized_payload(self):
        with self.assertRaises(ValueError):
            encode_message({"message": "x" * MAX_MESSAGE_BYTES})

    def test_rejects_empty_request_message(self):
        with self.assertRaises(ValueError):
            make_request("  ")

    def test_unsupported_request_type(self):
        self.assertEqual(
            make_response({"id": "2", "type": "unknown"}),
            {"id": "2", "status": "error", "error": "unsupported request type"},
        )


if __name__ == "__main__":
    unittest.main()
