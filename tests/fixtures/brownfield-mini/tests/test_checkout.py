import unittest

from src.checkout import charge_count


class ChargeCountTests(unittest.TestCase):
    def test_distinct_attempts_are_charged(self) -> None:
        self.assertEqual(2, charge_count(["attempt-1", "attempt-2"]))


if __name__ == "__main__":
    unittest.main()
