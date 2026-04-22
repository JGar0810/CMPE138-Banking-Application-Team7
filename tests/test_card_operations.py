import unittest
from datetime import date

from app.card_operations import CardBankingService


class CursorStub:
    def __init__(self, fetchone_values=None, lastrowid=101):
        self.fetchone_values = list(fetchone_values or [])
        self.executed = []
        self.lastrowid = lastrowid

    def execute(self, query, params=None):
        self.executed.append((" ".join(query.split()), params))

    def fetchone(self):
        if self.fetchone_values:
            return self.fetchone_values.pop(0)
        return None

    def close(self):
        pass


class ConnectionStub:
    def __init__(self, cursor_stub):
        self.cursor_stub = cursor_stub
        self.committed = False
        self.rolled_back = False

    def cursor(self, dictionary=False):
        return self.cursor_stub

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


class CardOperationsTests(unittest.TestCase):
    def test_request_new_card_success(self):
        cursor = CursorStub(
            fetchone_values=[
                {"account_id": 1, "customer_id": 1, "status": "active"},
                {"employee_id": 2, "status": "active"},
                None,
            ],
            lastrowid=77,
        )
        conn = ConnectionStub(cursor)
        service = CardBankingService(conn)
        result = service.request_new_card(1, "debit", requested_by=2, issue_date=date(2026, 4, 22))
        self.assertTrue(result.ok)
        self.assertEqual(result.payload["card_id"], 77)
        self.assertEqual(result.payload["card_type"], "debit")
        self.assertEqual(result.payload["expiry_date"], "2029-04-30")
        self.assertTrue(conn.committed)

    def test_request_new_card_rejects_closed_account(self):
        cursor = CursorStub(fetchone_values=[{"account_id": 1, "customer_id": 1, "status": "closed"}])
        conn = ConnectionStub(cursor)
        service = CardBankingService(conn)
        result = service.request_new_card(1, "credit")
        self.assertFalse(result.ok)
        self.assertIn("active account", result.message)
        self.assertTrue(conn.rolled_back)

    def test_report_card_lost_success(self):
        cursor = CursorStub(fetchone_values=[
            {"employee_id": 2, "status": "active"},
            {"card_id": 4, "account_id": 5, "card_number": "4444444444444444", "card_type": "debit", "status": "active"},
        ])
        conn = ConnectionStub(cursor)
        service = CardBankingService(conn)
        result = service.report_card_lost(card_number="4444444444444444", reported_by=2)
        self.assertTrue(result.ok)
        self.assertEqual(result.payload["status"], "blocked")
        self.assertTrue(conn.committed)

    def test_report_card_lost_already_blocked(self):
        cursor = CursorStub(fetchone_values=[
            {"card_id": 4, "account_id": 5, "card_number": "4444444444444444", "card_type": "debit", "status": "blocked"},
        ])
        conn = ConnectionStub(cursor)
        service = CardBankingService(conn)
        result = service.report_card_lost(card_id=4)
        self.assertTrue(result.ok)
        self.assertIn("already blocked", result.message)
        self.assertFalse(conn.committed)


if __name__ == "__main__":
    unittest.main()
