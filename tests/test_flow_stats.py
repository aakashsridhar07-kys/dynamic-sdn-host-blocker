import unittest
from dynamic_sdn_blocker.flow_stats import counter_delta
class TestRates(unittest.TestCase):
 def test_rate(self): self.assertEqual(counter_delta(10,100,20,300,2).packets_per_second,5)
