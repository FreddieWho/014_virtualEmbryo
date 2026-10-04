import unittest
import numpy as np
from scripts.t3_arch_two.fate import integer_donors


class FateInvariants(unittest.TestCase):
    def test_equal_state_shares_preserve_exact_rows(self):
        labels = np.array([0, 1, 1, 2, 2, 2])
        shares = np.bincount(labels, minlength=3) / len(labels)
        np.testing.assert_array_equal(integer_donors(labels, shares, 11), np.arange(len(labels)))

    def test_predicted_mass_changes_actual_rows_without_column_mixing(self):
        labels = np.repeat(np.arange(3), 10)
        donors = integer_donors(labels, np.array([.1, .2, .7]), 11)
        np.testing.assert_array_equal(np.bincount(labels[donors], minlength=3), [3, 6, 21])
        matrix = np.column_stack([np.arange(30), 100 + np.arange(30)])
        np.testing.assert_array_equal(matrix[donors, 1] - matrix[donors, 0], np.full(30, 100))


if __name__ == '__main__':
    unittest.main()
