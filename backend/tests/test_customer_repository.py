import unittest

from app.repositories.customer_repository import CustomerRepository


class CustomerRepositoryTests(unittest.TestCase):
    def test_normalize_phone_strips_whatsapp_prefix(self):
        normalized = CustomerRepository._normalize_phone("whatsapp:+573001234567")
        self.assertEqual(normalized, "+573001234567")

    def test_normalize_phone_adds_plus_prefix(self):
        normalized = CustomerRepository._normalize_phone("573001234567")
        self.assertEqual(normalized, "+573001234567")


if __name__ == "__main__":
    unittest.main()
