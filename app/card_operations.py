from __future__ import annotations

from calendar import monthrange
from datetime import date
from random import SystemRandom
from typing import Optional

from app.account_operations import OperationResult
from app.logger import log_action, log_error

_CARD_TYPES = {"debit", "credit"}
_RANDOM = SystemRandom()


class CardOperationError(Exception):
    pass


class CardBankingService:
    def __init__(self, connection):
        self.conn = connection

    def _last_day_same_month(self, year: int, month: int) -> date:
        return date(year, month, monthrange(year, month)[1])

    def _default_expiry(self, issue_date: date) -> date:
        return self._last_day_same_month(issue_date.year + 3, issue_date.month)

    def _generate_card_number(self) -> str:
        prefix = _RANDOM.choice(["4", "5"])
        remainder = "".join(str(_RANDOM.randrange(10)) for _ in range(15))
        return prefix + remainder

    def _employee_is_active(self, cursor, employee_id: Optional[int]) -> None:
        if employee_id is None:
            return
        cursor.execute("SELECT employee_id, status FROM Employee WHERE employee_id = %s", (employee_id,))
        employee = cursor.fetchone()
        if employee is None:
            raise CardOperationError(f"Employee {employee_id} does not exist.")
        if employee["status"] != "active":
            raise CardOperationError(f"Employee {employee_id} is not active.")

    def _get_account(self, cursor, account_id: int):
        cursor.execute("SELECT account_id, customer_id, status FROM Account WHERE account_id = %s FOR UPDATE", (account_id,))
        return cursor.fetchone()

    def _ensure_unique_card_number(self, cursor) -> str:
        for _ in range(25):
            candidate = self._generate_card_number()
            cursor.execute("SELECT card_id FROM Card WHERE card_number = %s", (candidate,))
            if cursor.fetchone() is None:
                return candidate
        raise CardOperationError("Unable to generate a unique card number. Please try again.")

    def request_new_card(self, account_id: int, card_type: str, requested_by: Optional[int] = None, issue_date: Optional[date] = None) -> OperationResult:
        action = f"request_new_card(account_id={account_id}, card_type={card_type})"
        cursor = self.conn.cursor(dictionary=True)
        try:
            normalized_type = card_type.strip().lower()
            if normalized_type not in _CARD_TYPES:
                raise CardOperationError("Card type must be 'debit' or 'credit'.")

            account = self._get_account(cursor, account_id)
            if account is None:
                raise CardOperationError(f"Account {account_id} does not exist.")
            if account["status"] != "active":
                raise CardOperationError("A new card can only be issued for an active account.")

            self._employee_is_active(cursor, requested_by)

            issue = issue_date or date.today()
            expiry = self._default_expiry(issue)
            card_number = self._ensure_unique_card_number(cursor)

            cursor.execute(
                """
                INSERT INTO Card (account_id, card_number, card_type, expiry_date, issue_date, status)
                VALUES (%s, %s, %s, %s, %s, 'active')
                """,
                (account_id, card_number, normalized_type, expiry, issue),
            )
            card_id = cursor.lastrowid
            self.conn.commit()

            log_action(requested_by or "system", action, f"created card_id={card_id}")
            return OperationResult(True, f"New {normalized_type} card issued successfully.", {"card_id": card_id, "account_id": account_id, "card_number": card_number, "card_type": normalized_type, "issue_date": issue.isoformat(), "expiry_date": expiry.isoformat(), "status": "active"})
        except Exception as exc:
            self.conn.rollback()
            log_error(requested_by or "system", action, str(exc))
            return OperationResult(False, str(exc))
        finally:
            cursor.close()

    def report_card_lost(self, *, card_number: Optional[str] = None, card_id: Optional[int] = None, reported_by: Optional[int] = None) -> OperationResult:
        action = f"report_card_lost(card_id={card_id}, card_number={card_number})"
        cursor = self.conn.cursor(dictionary=True)
        try:
            if (card_id is None and card_number is None) or (card_id is not None and card_number is not None):
                raise CardOperationError("Provide exactly one of card_id or card_number.")

            self._employee_is_active(cursor, reported_by)

            if card_id is not None:
                cursor.execute("SELECT card_id, account_id, card_number, card_type, status FROM Card WHERE card_id = %s FOR UPDATE", (card_id,))
            else:
                cursor.execute("SELECT card_id, account_id, card_number, card_type, status FROM Card WHERE card_number = %s FOR UPDATE", (card_number,))

            card = cursor.fetchone()
            if card is None:
                raise CardOperationError("Card not found.")

            if card["status"] == "blocked":
                log_action(reported_by or "system", action, f"already blocked card_id={card['card_id']}")
                return OperationResult(True, "Card was already blocked.", {"card_id": card["card_id"], "account_id": card["account_id"], "card_number": card["card_number"], "card_type": card["card_type"], "status": "blocked"})

            cursor.execute("UPDATE Card SET status = 'blocked' WHERE card_id = %s", (card["card_id"],))
            self.conn.commit()

            log_action(reported_by or "system", action, f"blocked card_id={card['card_id']}")
            return OperationResult(True, "Card reported lost and blocked successfully.", {"card_id": card["card_id"], "account_id": card["account_id"], "card_number": card["card_number"], "card_type": card["card_type"], "status": "blocked"})
        except Exception as exc:
            self.conn.rollback()
            log_error(reported_by or "system", action, str(exc))
            return OperationResult(False, str(exc))
        finally:
            cursor.close()
