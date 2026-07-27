import unittest

from src.settings_dialog import BUTTON_LABEL


class SettingsDialogTests(unittest.TestCase):
    def test_save_button_label(self) -> None:
        self.assertEqual("Save", BUTTON_LABEL)


if __name__ == "__main__":
    unittest.main()
