from decimal import Decimal
import unittest

from app.ahmad_ops import AhmadBankingService


class FakeCursor:
    def __init__(self, script):
        self.script = list(script)
        self.lastrowid = None
        self.executed = []

    def execute(self, query, params=None):
        self.executed.append((" ".join(query.split()), params))
        if not self.script:
            self.current = None
            return
        self.current = self.script.pop(0)
        self.lastrowid = self.current.get("lastrowid")

    def fetchone(self):
        if self.current is None:
            return None
        return self.current.get("fetchone")

    def close(self):
        pass


class FakeConnection:
    def __init__(self, script):
        self.script = script
        self.committed = False
        self.rolled_back = False
        self.closed = False
        self.cursor_obj = FakeCursor(script)

    def cursor(self, dictionary=True):
        return self.cursor_obj

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


class AhmadOpsTests(unittest.TestCase):
    def test_deposit_success(self):
        conn = FakeConnection([
            {"fetchone": {"employee_id": 2}},
            {"fetchone": {"account_id": 1, "customer_id": 1, "account_type": "checking", "balance": Decimal("5200.00"), "status": "active"}},
            {},
            {"lastrowid": 99},
        ])
        result = AhmadBankingService(conn).process_deposit(1, "250.00", 2, "ATM deposit")
        self.assertTrue(result.ok)
        self.assertEqual(result.payload["new_balance"], "5450.00")
        self.assertTrue(conn.committed)

    def test_withdrawal_insufficient_funds(self):
        conn = FakeConnection([
            {"fetchone": {"employee_id": 2}},
            {"fetchone": {"account_id": 5, "customer_id": 3, "account_type": "checking", "balance": Decimal("800.75"), "status": "active"}},
        ])
        result = AhmadBankingService(conn).process_withdrawal(5, "900.00", 2)
        self.assertFalse(result.ok)
        self.assertIn("Insufficient funds", result.message)
        self.assertTrue(conn.rolled_back)

    def test_open_account_with_opening_deposit(self):
        conn = FakeConnection([
            {"fetchone": {"customer_id": 1, "status": "active"}},
            {"fetchone": {"employee_id": 2}},
            {"lastrowid": 6},
            {"lastrowid": 12},
        ])
        result = AhmadBankingService(conn).open_account(1, "checking", "100.00", 2)
        self.assertTrue(result.ok)
        self.assertEqual(result.payload["account_id"], 6)
        self.assertTrue(conn.committed)

    def test_close_account_requires_zero_balance(self):
        conn = FakeConnection([
            {"fetchone": {"account_id": 1, "customer_id": 1, "account_type": "checking", "balance": Decimal("10.00"), "status": "active"}},
        ])
        result = AhmadBankingService(conn).close_account(1)
        self.assertFalse(result.ok)
        self.assertIn("must be $0.00", result.message)


if __name__ == "__main__":
    unittest.main()
