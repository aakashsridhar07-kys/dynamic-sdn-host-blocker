import unittest

from controller.security_policy import normalize_ipv4, validate_block_seconds


class SecurityPolicyTests(unittest.TestCase):
    def test_normalizes_ipv4(self):
        self.assertEqual(normalize_ipv4(" 10.20.0.1 "), "10.20.0.1")

    def test_rejects_invalid_or_unsupported_addresses(self):
        for value in ("not-an-ip", "2001:db8::1", "0.0.0.0", "224.0.0.1"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    normalize_ipv4(value)

    def test_validates_block_duration(self):
        self.assertEqual(validate_block_seconds(300), 300)
        self.assertEqual(validate_block_seconds(0), 0)
        for value in (-1, 65536, True, "300"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate_block_seconds(value)


if __name__ == "__main__":
    unittest.main()
