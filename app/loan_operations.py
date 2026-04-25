from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Optional


MONEY_PLACES = Decimal("0.01")


@dataclass
class OperationResult:
    ok: bool
    message: str
    payload: Optional[dict] = None


class LoanError(Exception):
    pass


class LoanService:
    def __init__(self, conn):
        self.conn = conn

    def _money(self, value: Any) -> Decimal:
        try:
            amount = Decimal(str(value)).quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)
        except (InvalidOperation, ValueError):
            raise LoanError("Invalid money amount.")

        if amount <= 0:
            raise LoanError("Amount must be greater than 0.")

        return amount

    def _rate(self, value: Any) -> Decimal:
        try:
            rate = Decimal(str(value)).quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)
        except (InvalidOperation, ValueError):
            raise LoanError("Invalid interest rate.")

        if rate < 0:
            raise LoanError("Interest rate cannot be negative.")

        return rate

    def _monthly_payment(
        self,
        principal: Decimal,
        annual_rate_percent: Decimal,
        months: int,
    ) -> Decimal:
        if months <= 0:
            raise LoanError("Loan term must be greater than 0 months.")

        monthly_rate = annual_rate_percent / Decimal("100") / Decimal("12")

        if monthly_rate == 0:
            payment = principal / Decimal(months)
        else:
            factor = (Decimal("1") + monthly_rate) ** months
            payment = principal * (monthly_rate * factor) / (factor - Decimal("1"))

        return payment.quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)

    def _validate_customer(self, cursor, customer_id: int):
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
            raise LoanError(f"Customer {customer_id} does not exist.")

        if customer["status"] != "active":
            raise LoanError("Customer account must be active.")

    def _validate_loan_officer_or_manager(self, cursor, employee_id: int):
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
            raise LoanError(f"Employee {employee_id} does not exist.")

        if employee["status"] != "active":
            raise LoanError("Employee account is not active.")

        if employee["role"] not in ("loan_officer", "manager"):
            raise LoanError("Only loan officers or managers can process loans.")

    def apply_for_loan(
        self,
        customer_id: int,
        loan_amount: Any,
        interest_rate: Any,
        loan_terms: Any,
    ) -> OperationResult:
        cursor = self.conn.cursor(dictionary=True)

        try:
            principal = self._money(loan_amount)
            rate = self._rate(interest_rate)

            try:
                months = int(loan_terms)
            except (TypeError, ValueError):
                raise LoanError("Loan term must be a whole number of months.")

            if months <= 0:
                raise LoanError("Loan term must be greater than 0 months.")

            self._validate_customer(cursor, customer_id)

            monthly_payment = self._monthly_payment(principal, rate, months)

            cursor.execute(
                """
                INSERT INTO Loan
                    (
                        customer_id,
                        loan_amount,
                        interest_rate,
                        loan_term_months,
                        monthly_payment,
                        remaining_balance,
                        status
                    )
                VALUES
                    (%s, %s, %s, %s, %s, %s, 'pending')
                """,
                (
                    customer_id,
                    principal,
                    rate,
                    months,
                    monthly_payment,
                    principal,
                ),
            )

            loan_id = cursor.lastrowid
            self.conn.commit()

            return OperationResult(
                True,
                "Loan application submitted successfully.",
                {
                    "loan_id": loan_id,
                    "customer_id": customer_id,
                    "loan_amount": str(principal),
                    "interest_rate": str(rate),
                    "loan_term_months": months,
                    "monthly_payment": str(monthly_payment),
                    "remaining_balance": str(principal),
                    "status": "pending",
                },
            )

        except Exception as exc:
            self.conn.rollback()
            return OperationResult(False, str(exc))

        finally:
            cursor.close()

    def review_loans(self) -> OperationResult:
        cursor = self.conn.cursor(dictionary=True)

        try:
            cursor.execute(
                """
                SELECT
                    l.loan_id,
                    l.customer_id,
                    c.username,
                    l.loan_amount,
                    l.interest_rate,
                    l.loan_term_months,
                    l.monthly_payment,
                    l.remaining_balance,
                    l.status,
                    l.application_date,
                    l.decision_date,
                    l.processed_by
                FROM Loan l
                JOIN Customer c ON l.customer_id = c.customer_id
                WHERE l.status = 'pending'
                ORDER BY l.application_date ASC, l.loan_id ASC
                """
            )

            loans = cursor.fetchall()

            return OperationResult(
                True,
                "Pending loan applications retrieved.",
                {"loans": loans},
            )

        except Exception as exc:
            return OperationResult(False, str(exc))

        finally:
            cursor.close()

    def approve_loan(self, loan_id: int, processed_by: int) -> OperationResult:
        cursor = self.conn.cursor(dictionary=True)

        try:
            self._validate_loan_officer_or_manager(cursor, processed_by)

            cursor.execute(
                """
                SELECT loan_id, customer_id, loan_amount, status
                FROM Loan
                WHERE loan_id = %s
                FOR UPDATE
                """,
                (loan_id,),
            )
            loan = cursor.fetchone()

            if loan is None:
                raise LoanError(f"Loan {loan_id} does not exist.")

            if loan["status"] != "pending":
                raise LoanError("Only pending loans can be approved.")

            cursor.execute(
                """
                UPDATE Loan
                SET
                    status = 'approved',
                    processed_by = %s,
                    decision_date = NOW()
                WHERE loan_id = %s
                """,
                (processed_by, loan_id),
            )

            self.conn.commit()

            return OperationResult(
                True,
                "Loan approved successfully.",
                {
                    "loan_id": loan_id,
                    "processed_by": processed_by,
                    "new_status": "approved",
                },
            )

        except Exception as exc:
            self.conn.rollback()
            return OperationResult(False, str(exc))

        finally:
            cursor.close()

    def reject_loan(self, loan_id: int, processed_by: int) -> OperationResult:
        cursor = self.conn.cursor(dictionary=True)

        try:
            self._validate_loan_officer_or_manager(cursor, processed_by)

            cursor.execute(
                """
                SELECT loan_id, customer_id, loan_amount, status
                FROM Loan
                WHERE loan_id = %s
                FOR UPDATE
                """,
                (loan_id,),
            )
            loan = cursor.fetchone()

            if loan is None:
                raise LoanError(f"Loan {loan_id} does not exist.")

            if loan["status"] != "pending":
                raise LoanError("Only pending loans can be rejected.")

            cursor.execute(
                """
                UPDATE Loan
                SET
                    status = 'rejected',
                    processed_by = %s,
                    decision_date = NOW()
                WHERE loan_id = %s
                """,
                (processed_by, loan_id),
            )

            self.conn.commit()

            return OperationResult(
                True,
                "Loan rejected successfully.",
                {
                    "loan_id": loan_id,
                    "processed_by": processed_by,
                    "new_status": "rejected",
                },
            )

        except Exception as exc:
            self.conn.rollback()
            return OperationResult(False, str(exc))

        finally:
            cursor.close()