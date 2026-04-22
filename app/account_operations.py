from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Optional

from app.logger import log_action, log_error

MONEY_PLACES = Decimal("0.01")
VALID_ACCOUNT_TYPES = {"checking", "savings"}


class BankingError(Exception):
    pass


@dataclass
class OperationResult:
    ok: bool
    message: str
    payload: Optional[dict[str, Any]] = None


class AccountBankingService:
    def __init__(self, connection):
        self.conn = connection

    def _q(self, amount: Any) -> Decimal:
        try:
            value = Decimal(str(amount)).quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)
        except Exception as exc:
            raise BankingError("Amount must be a valid number.") from exc
        if value <= 0:
            raise BankingError("Amount must be greater than 0.")
        return value

    def _get_account_for_update(self, cursor, account_id: int):
        cursor.execute(
            """
            SELECT account_id, customer_id, account_type, balance, status
            FROM Account
            WHERE account_id = %s
            FOR UPDATE
            """,
            (account_id,),
        )
        return cursor.fetchone()

    def _validate_employee_role(self, cursor, employee_id: Optional[int], required_role: str) -> None:
        if employee_id is None:
            return
        cursor.execute(
            """
            SELECT employee_id
            FROM Employee
            WHERE employee_id = %s AND role = %s AND status = 'active'
            """,
            (employee_id, required_role),
        )
        if cursor.fetchone() is None:
            raise BankingError(f"Employee {employee_id} is not an active {required_role}.")

    def open_account(self, customer_id: int, account_type: str, opening_deposit: Any = 0, processed_by: Optional[int] = None) -> OperationResult:
        account_type = account_type.strip().lower()
        if account_type not in VALID_ACCOUNT_TYPES:
            return OperationResult(False, "Account type must be 'checking' or 'savings'.")

        deposit = Decimal("0.00") if Decimal(str(opening_deposit)) == 0 else self._q(opening_deposit)
        cursor = self.conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT customer_id, status FROM Customer WHERE customer_id = %s", (customer_id,))
            customer = cursor.fetchone()
            if customer is None:
                raise BankingError(f"Customer {customer_id} does not exist.")
            if customer["status"] != "active":
                raise BankingError(f"Customer {customer_id} is not active.")

            if deposit > 0:
                self._validate_employee_role(cursor, processed_by, "teller")

            cursor.execute(
                """
                INSERT INTO Account (customer_id, account_type, balance, status)
                VALUES (%s, %s, %s, 'active')
                """,
                (customer_id, account_type, deposit),
            )
            account_id = cursor.lastrowid

            if deposit > 0:
                cursor.execute(
                    """
                    INSERT INTO `Transaction` (account_id, transaction_type, amount, description, processed_by)
                    VALUES (%s, 'deposit', %s, %s, %s)
                    """,
                    (account_id, deposit, "Opening deposit", processed_by),
                )

            self.conn.commit()
            log_action(f"customer:{customer_id}", "open_account", f"success account_id={account_id}")
            return OperationResult(True, f"Account {account_id} opened successfully.", {"account_id": account_id, "balance": str(deposit), "account_type": account_type})
        except Exception as exc:
            self.conn.rollback()
            log_error(f"customer:{customer_id}", "open_account", str(exc))
            return OperationResult(False, str(exc))
        finally:
            cursor.close()

    def process_deposit(self, account_id: int, amount: Any, processed_by: Optional[int] = None, description: str = "CLI deposit") -> OperationResult:
        cursor = self.conn.cursor(dictionary=True)
        try:
            amount_dec = self._q(amount)
            self._validate_employee_role(cursor, processed_by, "teller")
            account = self._get_account_for_update(cursor, account_id)
            if account is None:
                raise BankingError(f"Account {account_id} does not exist.")
            if account["status"] != "active":
                raise BankingError(f"Account {account_id} is not active.")

            new_balance = (Decimal(str(account["balance"])) + amount_dec).quantize(MONEY_PLACES)
            cursor.execute("UPDATE Account SET balance = %s WHERE account_id = %s", (new_balance, account_id))
            cursor.execute(
                """
                INSERT INTO `Transaction` (account_id, transaction_type, amount, description, processed_by)
                VALUES (%s, 'deposit', %s, %s, %s)
                """,
                (account_id, amount_dec, description, processed_by),
            )
            transaction_id = cursor.lastrowid
            self.conn.commit()
            log_action(f"account:{account_id}", "process_deposit", f"success amount={amount_dec} balance={new_balance}")
            return OperationResult(True, f"Deposit complete. New balance: ${new_balance}", {"transaction_id": transaction_id, "new_balance": str(new_balance)})
        except Exception as exc:
            self.conn.rollback()
            log_error(f"account:{account_id}", "process_deposit", str(exc))
            return OperationResult(False, str(exc))
        finally:
            cursor.close()

    def process_withdrawal(self, account_id: int, amount: Any, processed_by: Optional[int] = None, description: str = "CLI withdrawal") -> OperationResult:
        cursor = self.conn.cursor(dictionary=True)
        try:
            amount_dec = self._q(amount)
            self._validate_employee_role(cursor, processed_by, "teller")
            account = self._get_account_for_update(cursor, account_id)
            if account is None:
                raise BankingError(f"Account {account_id} does not exist.")
            if account["status"] != "active":
                raise BankingError(f"Account {account_id} is not active.")

            current_balance = Decimal(str(account["balance"]))
            if current_balance < amount_dec:
                raise BankingError(f"Insufficient funds. Current balance is ${current_balance.quantize(MONEY_PLACES)}.")

            new_balance = (current_balance - amount_dec).quantize(MONEY_PLACES)
            cursor.execute("UPDATE Account SET balance = %s WHERE account_id = %s", (new_balance, account_id))
            cursor.execute(
                """
                INSERT INTO `Transaction` (account_id, transaction_type, amount, description, processed_by)
                VALUES (%s, 'withdrawal', %s, %s, %s)
                """,
                (account_id, amount_dec, description, processed_by),
            )
            transaction_id = cursor.lastrowid
            self.conn.commit()
            log_action(f"account:{account_id}", "process_withdrawal", f"success amount={amount_dec} balance={new_balance}")
            return OperationResult(True, f"Withdrawal complete. New balance: ${new_balance}", {"transaction_id": transaction_id, "new_balance": str(new_balance)})
        except Exception as exc:
            self.conn.rollback()
            log_error(f"account:{account_id}", "process_withdrawal", str(exc))
            return OperationResult(False, str(exc))
        finally:
            cursor.close()

    def close_account(self, account_id: int) -> OperationResult:
        cursor = self.conn.cursor(dictionary=True)
        try:
            account = self._get_account_for_update(cursor, account_id)
            if account is None:
                raise BankingError(f"Account {account_id} does not exist.")
            if account["status"] == "closed":
                raise BankingError(f"Account {account_id} is already closed.")
            if Decimal(str(account["balance"])) != Decimal("0.00"):
                raise BankingError("Account balance must be $0.00 before closing the account.")

            cursor.execute("SELECT COUNT(*) AS active_cards FROM Card WHERE account_id = %s AND status = 'active'", (account_id,))
            card_row = cursor.fetchone()
            if card_row and int(card_row["active_cards"]) > 0:
                raise BankingError("Account still has active cards. Block or expire the cards before closing the account.")

            cursor.execute("UPDATE Account SET status = 'closed' WHERE account_id = %s", (account_id,))
            self.conn.commit()
            log_action(f"account:{account_id}", "close_account", "success")
            return OperationResult(True, f"Account {account_id} closed successfully.")
        except Exception as exc:
            self.conn.rollback()
            log_error(f"account:{account_id}", "close_account", str(exc))
            return OperationResult(False, str(exc))
        finally:
            cursor.close()
