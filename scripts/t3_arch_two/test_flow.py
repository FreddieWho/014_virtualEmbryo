import unittest
import numpy as np
import torch
from scripts.t3_arch_two.flow import ResidualField, integrate


class FlowInvariants(unittest.TestCase):
    def test_null_is_exact_identity_after_integration(self):
        torch.manual_seed(9)
        model = ResidualField(7, 4, 16)
        base = np.array([[0., 2., 0., 1., 0., 3., 4.], [1., 0., 1., 0., 4., 0., 2.]], dtype=np.float32)
        result = integrate(model, base, np.zeros(7), np.ones(7), np.zeros(4), 8)
        np.testing.assert_array_equal(result, base)

    def test_condition_changes_zero_rna_cells_and_preserves_absent_support(self):
        torch.manual_seed(13)
        model = ResidualField(7, 4, 16)
        model.support[-1] = 0.
        base = np.zeros((3, 7), dtype=np.float32)
        # Field is condition-driven even when every expression entry is zero.
        t = torch.full((3,), .5)
        v = model(torch.zeros(3, 7), torch.zeros(3, 7), t, torch.ones(3, 4))
        self.assertGreater(float(v[:, :-1].detach().abs().max()), 0.)
        np.testing.assert_array_equal(v[:, -1].detach().numpy(), np.zeros(3))
        result = integrate(model, base, np.zeros(7), np.ones(7), np.ones(4), 8)
        self.assertTrue(np.isfinite(result).all())
        self.assertGreaterEqual(float(result.min()), 0.)


if __name__ == '__main__':
    unittest.main()
