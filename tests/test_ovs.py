import subprocess
import unittest
from types import SimpleNamespace

from dynamic_sdn_blocker.ovs import OVSRuleManager


class TestOVSRuleManager(unittest.TestCase):
    def setUp(self):
        self.calls = []

        def fake_runner(cmd, **kwargs):
            self.calls.append((cmd, kwargs))
            return SimpleNamespace(stdout="ok\n")

        self.manager = OVSRuleManager(runner=fake_runner)

    def test_block_adds_drop_flow(self):
        self.assertEqual(self.manager.block("10.10.0.11"), "ok")
        cmd, kwargs = self.calls[-1]
        self.assertIn("add-flow", cmd)
        self.assertIn("nw_src=10.10.0.11,actions=drop", cmd[-1])
        self.assertTrue(kwargs["check"])

    def test_unblock_deletes_owned_flow(self):
        self.assertEqual(self.manager.unblock("10.10.0.12"), "ok")
        cmd, _ = self.calls[-1]
        self.assertIn("del-flows", cmd)
        self.assertIn("cookie=0xD1A0/-1", cmd[-1])

    def test_rejects_ip_outside_lab(self):
        with self.assertRaises(ValueError):
            self.manager.block("192.168.1.10")

    def test_runner_errors_propagate(self):
        def failing_runner(cmd, **kwargs):
            raise subprocess.CalledProcessError(1, cmd)

        manager = OVSRuleManager(runner=failing_runner)
        with self.assertRaises(subprocess.CalledProcessError):
            manager.block("10.10.0.11")


if __name__ == "__main__":
    unittest.main()
