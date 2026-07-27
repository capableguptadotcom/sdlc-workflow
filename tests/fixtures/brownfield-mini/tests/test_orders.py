import unittest

from src.orders import shipment_status


class ShipmentStatusTests(unittest.TestCase):
    def test_order_with_destination_is_ready(self) -> None:
        self.assertEqual("ready", shipment_status("Portland"))

    def test_order_without_destination_is_draft(self) -> None:
        self.assertEqual("draft", shipment_status(""))


if __name__ == "__main__":
    unittest.main()
