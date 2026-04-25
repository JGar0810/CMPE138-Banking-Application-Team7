from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

MONEY_PLACES = Decimal("0.01")


@dataclass
class OperationResult:
    ok: bool
    message: str
    payload: Optional[dict] = None


class BankingError(Exception):
    pass


class AccountBankingService:
    def __init__(self, conn):
        self.conn = conn

    def _q(self, amount: Any) -> Decimal:
        try:
            value = Decimal(str(amount)).quantize(MONEY_PLACES)
        except (InvalidOperation, ValueError):
            raise BankingError("Invalid amount.")

        if value < 0:
            raise BankingError("Amount cannot be negative.")

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

    def _validate_teller_if_provided(self, cursor, employee_id: Optional[int]):
        if employee_id is None:
            return

        cursor.execute(
            """
            SELECT employee_id, role, status
            FROM Employee
            WHERE employee_id = %s
            """,
            (employee_id,),
        )
        employee = cursor.fetchone()

        if employee is None:
            raise BankingError(f"Employee {employee_id} does not exist.")

        if employee["status"] != "active":
            raise BankingError("Employee is not active.")

        if employee["role"] != "teller":
            raise BankingError("Employee must be a teller to process this operation.")

    def open_account(
        self,
        customer_id: int,
        account_type: str,
        opening_deposit: Any = "0",
        processed_by: Optional[int] = None,
    ) -> OperationResult:
        cursor = self.conn.cursor(dictionary=True)

        try:
            account_type = account_type.lower().strip()
            if account_type not in ("checking", "savings"):
                raise BankingError("Account type must be checking or savings.")

            deposit_amount = self._q(opening_deposit)

            cursor.execute(
                """
                SELECT customer_id, status
                FROM Customer
                WHERE customer_id = %s
                """,
                (customer_id,),
            )
            customer = cursor.fetchone()

            if customer is None:
                raise BankingError(f"Customer {customer_id} does not exist.")

            if customer["status"] != "active":
                raise BankingError("Customer must be active to open an account.")

            self._validate_teller_if_provided(cursor, processed_by)

            cursor.execute(
                """
                INSERT INTO Account (customer_id, account_type, balance, status)
                VALUES (%s, %s, %s, 'active')
                """,
                (customer_id, account_type, deposit_amount),
            )

            account_id = cursor.lastrowid

            if deposit_amount > 0:
                cursor.execute(
                    """
                    INSERT INTO `Transaction`
                        (account_id, transaction_type, amount, description, processed_by)
                    VALUES
                        (%s, 'deposit', %s, %s, %s)
                    """,
                    (
                        account_id,
                        deposit_amount,
                        "Opening deposit",
                        processed_by,
                    ),
                )

            self.conn.commit()

            return OperationResult(
                True,
                "Account opened successfully.",
                {
                    "account_id": account_id,
                    "customer_id": customer_id,
                    "account_type": account_type,
                    "opening_balance": str(deposit_amount),
                },
            )

        except Exception as exc:
            self.conn.rollback()
            return OperationResult(False, str(exc))

        finally:
            cursor.close()

    def process_deposit(
        self,
        account_id: int,
        amount: Any,
        processed_by: Optional[int] = None,
        description: str = "CLI deposit",
    ) -> OperationResult:
        cursor = self.conn.cursor(dictionary=True)

        try:
            amount_dec = self._q(amount)
            if amount_dec <= 0:
                raise BankingError("Deposit amount must be greater than 0.")

            self._validate_teller_if_provided(cursor, processed_by)

            account = self._get_account_for_update(cursor, account_id)

            if account is None:
                raise BankingError(f"Account {account_id} does not exist.")

            if account["status"] != "active":
                raise BankingError("Account must be active.")

            old_balance = Decimal(str(account["balance"]))
            new_balance = (old_balance + amount_dec).quantize(MONEY_PLACES)

            cursor.execute(
                """
                UPDATE Account
                SET balance = %s
                WHERE account_id = %s
                """,
                (new_balance, account_id),
            )

            cursor.execute(
                """
                INSERT INTO `Transaction`
                    (account_id, transaction_type, amount, description, processed_by)
                VALUES
                    (%s, 'deposit', %s, %s, %s)
                """,
                (account_id, amount_dec, description, processed_by),
            )

            self.conn.commit()

            return OperationResult(
                True,
                "Deposit processed successfully.",
                {
                    "account_id": account_id,
                    "old_balance": str(old_balance),
                    "deposit_amount": str(amount_dec),
                    "new_balance": str(new_balance),
                },
            )

        except Exception as exc:
            self.conn.rollback()
            return OperationResult(False, str(exc))

        finally:
            cursor.close()

    def process_withdrawal(
        self,
        account_id: int,
        amount: Any,
        processed_by: Optional[int] = None,
        description: str = "CLI withdrawal",
    ) -> OperationResult:
        cursor = self.conn.cursor(dictionary=True)

        try:
            amount_dec = self._q(amount)
            if amount_dec <= 0:
                raise BankingError("Withdrawal amount must be greater than 0.")

            self._validate_teller_if_provided(cursor, processed_by)

            account = self._get_account_for_update(cursor, account_id)

            if account is None:
                raise BankingError(f"Account {account_id} does not exist.")

            if account["status"] != "active":
                raise BankingError("Account must be active.")

            old_balance = Decimal(str(account["balance"]))

            if old_balance < amount_dec:
                raise BankingError("Insufficient funds.")

            new_balance = (old_balance - amount_dec).quantize(MONEY_PLACES)

            cursor.execute(
                """
                UPDATE Account
                SET balance = %s
                WHERE account_id = %s
                """,
                (new_balance, account_id),
            )

            cursor.execute(
                """
                INSERT INTO `Transaction`
                    (account_id, transaction_type, amount, description, processed_by)
                VALUES
                    (%s, 'withdrawal', %s, %s, %s)
                """,
                (account_id, amount_dec, description, processed_by),
            )

            self.conn.commit()

            return OperationResult(
                True,
                "Withdrawal processed successfully.",
                {
                    "account_id": account_id,
                    "old_balance": str(old_balance),
                    "withdrawal_amount": str(amount_dec),
                    "new_balance": str(new_balance),
                },
            )

        except Exception as exc:
            self.conn.rollback()
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
                raise BankingError("Account is already closed.")

            balance = Decimal(str(account["balance"]))

            if balance != Decimal("0.00"):
                raise BankingError("Account balance must be 0 before closing.")

            cursor.execute(
                """
                SELECT COUNT(*) AS active_card_count
                FROM Card
                WHERE account_id = %s
                  AND status = 'active'
                """,
                (account_id,),
            )
            row = cursor.fetchone()

            if row and row["active_card_count"] > 0:
                raise BankingError("Cannot close account with active linked cards.")

            cursor.execute(
                """
                UPDATE Account
                SET status = 'closed'
                WHERE account_id = %s
                """,
                (account_id,),
            )

            self.conn.commit()

            return OperationResult(
                True,
                "Account closed successfully.",
                {"account_id": account_id, "status": "closed"},
            )

        except Exception as exc:
            self.conn.rollback()
            return OperationResult(False, str(exc))

        finally:
            cursor.close()

    def transfer_funds(
        self,
        from_account_id: int,
        to_account_id: int,
        amount: Any,
        processed_by: Optional[int] = None,
    ) -> OperationResult:
        cursor = self.conn.cursor(dictionary=True)

        try:
            amount_dec = self._q(amount)
            if amount_dec <= 0:
                raise BankingError("Transfer amount must be greater than 0.")

            if from_account_id == to_account_id:
                raise BankingError("Source and destination accounts must be different.")

            self._validate_teller_if_provided(cursor, processed_by)

            # BEGIN is handled by MySQL Connector because autocommit is disabled.
            # The SELECT ... FOR UPDATE statements lock both account rows.
            from_account = self._get_account_for_update(cursor, from_account_id)
            to_account = self._get_account_for_update(cursor, to_account_id)

            if from_account is None:
                raise BankingError(f"Source account {from_account_id} does not exist.")

            if to_account is None:
                raise BankingError(f"Destination account {to_account_id} does not exist.")

            if from_account["status"] != "active":
                raise BankingError("Source account must be active.")

            if to_account["status"] != "active":
                raise BankingError("Destination account must be active.")

            from_old_balance = Decimal(str(from_account["balance"]))
            to_old_balance = Decimal(str(to_account["balance"]))

            if from_old_balance < amount_dec:
                raise BankingError("Insufficient funds for transfer.")

            from_new_balance = (from_old_balance - amount_dec).quantize(MONEY_PLACES)
            to_new_balance = (to_old_balance + amount_dec).quantize(MONEY_PLACES)

            cursor.execute(
                """
                UPDATE Account
                SET balance = %s
                WHERE account_id = %s
                """,
                (from_new_balance, from_account_id),
            )

            cursor.execute(
                """
                UPDATE Account
                SET balance = %s
                WHERE account_id = %s
                """,
                (to_new_balance, to_account_id),
            )

            cursor.execute(
                """
                INSERT INTO `Transaction`
                    (account_id, transaction_type, amount, description, processed_by)
                VALUES
                    (%s, 'transfer_out', %s, %s, %s)
                """,
                (
                    from_account_id,
                    amount_dec,
                    f"Transfer to account {to_account_id}",
                    processed_by,
                ),
            )

            cursor.execute(
                """
                INSERT INTO `Transaction`
                    (account_id, transaction_type, amount, description, processed_by)
                VALUES
                    (%s, 'transfer_in', %s, %s, %s)
                """,
                (
                    to_account_id,
                    amount_dec,
                    f"Transfer from account {from_account_id}",
                    processed_by,
                ),
            )

            # COMMIT saves both balance updates and both transaction records together.
            self.conn.commit()

            return OperationResult(
                True,
                "Transfer completed successfully.",
                {
                    "from_account_id": from_account_id,
                    "to_account_id": to_account_id,
                    "amount": str(amount_dec),
                    "from_old_balance": str(from_old_balance),
                    "from_new_balance": str(from_new_balance),
                    "to_old_balance": str(to_old_balance),
                    "to_new_balance": str(to_new_balance),
                },
            )

        except Exception as exc:
            # ROLLBACK prevents partial transfers if any update/insert fails.
            self.conn.rollback()
            return OperationResult(False, str(exc))

        finally:
            cursor.close()