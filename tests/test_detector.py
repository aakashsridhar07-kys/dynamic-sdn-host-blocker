import unittest
from dynamic_sdn_blocker.detector import SynRateDetector
class TestDetector(unittest.TestCase):
 def test_threshold(self):
  d=SynRateDetector('10.10.0.0/24',.4,5,2); self.assertIsNone(d.observe_syn('10.10.0.11',1)); self.assertIsNone(d.observe_syn('10.10.0.11',1.1)); self.assertIsNotNone(d.observe_syn('10.10.0.11',1.2))
 def test_outside_cidr(self): self.assertIsNone(SynRateDetector('10.10.0.0/24').observe_syn('192.168.1.1',1))
if __name__=='__main__': unittest.main()
