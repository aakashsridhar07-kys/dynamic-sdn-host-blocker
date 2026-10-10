import tempfile
import unittest
from pathlib import Path

from dynamic_sdn_blocker.blocklist import Blocklist


class TestBlocklist(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        database = Path(self.temp_dir.name) / "blocklist.sqlite3"
        self.blocklist = Blocklist(str(database))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_block_and_unblock(self):
        self.blocklist.block("10.10.0.11", 60, "test threshold")
        self.assertTrue(self.blocklist.is_blocked("10.10.0.11"))
        self.assertTrue(self.blocklist.unblock("10.10.0.11"))
        self.assertFalse(self.blocklist.is_blocked("10.10.0.11"))

    def test_expired_entry_is_not_blocked(self):
        self.blocklist.block("10.10.0.12", 60, "test expiry")
        self.assertFalse(self.blocklist.is_blocked("10.10.0.12", now=10**12))
        self.assertEqual(self.blocklist.expire(now=10**12), 1)

    def test_invalid_duration_rejected(self):
        with self.assertRaises(ValueError):
            self.blocklist.block("10.10.0.13", 0, "invalid duration")

    def test_invalid_ip_rejected(self):
        with self.assertRaises(ValueError):
            self.blocklist.block("not-an-ip", 60, "invalid IP")


if __name__ == "__main__":
    unittest.main()
