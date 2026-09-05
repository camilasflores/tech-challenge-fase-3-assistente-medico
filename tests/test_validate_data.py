import unittest

from fine_tuning.validate_data import validate_faq, validate_patients, validate_privacy


class ValidateDataTest(unittest.TestCase):
    def test_synthetic_patients_are_valid(self) -> None:
        self.assertEqual(validate_patients(), 5)

    def test_internal_faq_is_valid(self) -> None:
        self.assertEqual(validate_faq(), 20)

    def test_dataset_does_not_contain_common_personal_identifiers(self) -> None:
        validate_privacy()


if __name__ == "__main__":
    unittest.main()
