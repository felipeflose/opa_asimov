import unittest
from src.agents.finops_guardian import FinOpsGuardian

class TestFinOpsGuardian(unittest.TestCase):
    def test_token_estimation(self):
        guardian = FinOpsGuardian()
        tokens = guardian.estimate_tokens("Hello World")
        self.assertEqual(tokens, 11 // 4)

    def test_execution_approval(self):
        # Mocking GCS to return 0 usage
        guardian = FinOpsGuardian(cost_limit=1.0)
        approved, msg = guardian.check_execution(estimated_tokens=100, estimated_infra_cost=0.5)
        self.assertTrue(approved)
        
        # Over limit
        approved, msg = guardian.check_execution(estimated_tokens=100, estimated_infra_cost=1.5)
        self.assertFalse(approved)

if __name__ == '__main__':
    unittest.main()
