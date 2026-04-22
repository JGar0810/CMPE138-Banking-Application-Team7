# SJSU CMPE 138 SPRING 2026 TEAM7

from decimal import Decimal
from app.logger import log_action, log_error


class EvanBankingService:
    def __init__(self, conn):
        self.conn = conn

    def view_accounts(self, customer_id):
        cursor = self.conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT account_id, account_type, balance, date_opened, status
                FROM Account
                WHERE customer_id = %s
                ORDER BY account_id
            """, (customer_id,))
            rows = cursor.fetchall()
            log_action(f"customer:{customer_id}", "VIEW_ACCOUNTS", f"Returned {len(rows)} row(s)")
            return {"ok": True, "message": "Accounts retrieved.", "rows": rows}
        except Exception as e:
            log_error(f"customer:{customer_id}", "VIEW_ACCOUNTS", str(e))
            return {"ok": False, "message": str(e), "rows": []}
        finally:
            cursor.close()

    def view_transactions(self, customer_id):
        cursor = self.conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT
                    t.transaction_id,
                    t.account_id,
                    t.transaction_type,
                    t.amount,
                    t.transaction_date,
                    t.description
                FROM `Transaction` t
                JOIN Account a ON t.account_id = a.account_id
                WHERE a.customer_id = %s
                ORDER BY t.transaction_date DESC, t.transaction_id DESC
            """, (customer_id,))
            rows = cursor.fetchall()
            log_action(f"customer:{customer_id}", "VIEW_TRANSACTIONS", f"Returned {len(rows)} row(s)")
            return {"ok": True, "message": "Transactions retrieved.", "rows": rows}
        except Exception as e:
            log_error(f"customer:{customer_id}", "VIEW_TRANSACTIONS", str(e))
            return {"ok": False, "message": str(e), "rows": []}
        finally:
            cursor.close()

    def update_profile(self, customer_id, address=None, phone=None, email=None):
        cursor = self.conn.cursor(dictionary=True)
        try:
            updates = []
            params = []

            if address:
                updates.append("address = %s")
                params.append(address)
            if phone:
                updates.append("phone = %s")
                params.append(phone)
            if email:
                updates.append("email = %s")
                params.append(email)

            if not updates:
                return {"ok": False, "message": "No changes entered."}

            params.append(customer_id)

            query = f"""
                UPDATE Customer
                SET {", ".join(updates)}
                WHERE customer_id = %s
            """
            cursor.execute(query, tuple(params))
            self.conn.commit()

            log_action(f"customer:{customer_id}", "UPDATE_PROFILE", "Profile updated")
            return {"ok": True, "message": "Profile updated successfully."}
        except Exception as e:
            self.conn.rollback()
            log_error(f"customer:{customer_id}", "UPDATE_PROFILE", str(e))
            return {"ok": False, "message": str(e)}
        finally:
            cursor.close()

    def apply_for_loan(self, customer_id, loan_amount, interest_rate, loan_term_months):
        cursor = self.conn.cursor(dictionary=True)
        try:
            try:
                loan_amount = float(str(loan_amount).replace(",", ""))
                interest_rate = float(str(interest_rate).replace(",", ""))
                loan_term_months = int(str(loan_term_months).strip())
            except ValueError:
                return {"ok": False, "message": "Enter valid numbers for loan amount, interest rate, and loan term."}

            if loan_amount <= 0:
                return {"ok": False, "message": "Loan amount must be positive."}
            if interest_rate < 0:
                return {"ok": False, "message": "Interest rate cannot be negative."}
            if loan_term_months <= 0:
                return {"ok": False, "message": "Loan term must be positive."}

            monthly_rate = interest_rate / 100 / 12

            if monthly_rate == 0:
                monthly_payment = round(loan_amount / loan_term_months, 2)
            else:
                monthly_payment = round(
                    (loan_amount * monthly_rate * (1 + monthly_rate) ** loan_term_months) /
                    (((1 + monthly_rate) ** loan_term_months) - 1),
                    2
                )

            cursor.execute("""
                INSERT INTO Loan
                (customer_id, loan_amount, interest_rate, loan_term_months, monthly_payment, remaining_balance, status)
                VALUES (%s, %s, %s, %s, %s, %s, 'pending')
            """, (
                customer_id,
                loan_amount,
                interest_rate,
                loan_term_months,
                monthly_payment,
                loan_amount
            ))

            self.conn.commit()
            loan_id = cursor.lastrowid

            log_action(f"customer:{customer_id}", "APPLY_LOAN", f"loan_id={loan_id}")
            return {
                "ok": True,
                "message": "Loan application submitted successfully.",
                "loan_id": loan_id,
                "monthly_payment": monthly_payment
            }

        except Exception as e:
            self.conn.rollback()
            log_error(f"customer:{customer_id}", "APPLY_LOAN", str(e))
            return {"ok": False, "message": str(e)}
        finally:
            cursor.close()

    def view_loan_status(self, customer_id):
        cursor = self.conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT
                    loan_id,
                    loan_amount,
                    interest_rate,
                    loan_term_months,
                    monthly_payment,
                    remaining_balance,
                    status,
                    application_date,
                    decision_date
                FROM Loan
                WHERE customer_id = %s
                ORDER BY loan_id DESC
            """, (customer_id,))
            rows = cursor.fetchall()

            log_action(f"customer:{customer_id}", "VIEW_LOAN_STATUS", f"Returned {len(rows)} row(s)")
            return {"ok": True, "message": "Loan status retrieved.", "rows": rows}
        except Exception as e:
            log_error(f"customer:{customer_id}", "VIEW_LOAN_STATUS", str(e))
            return {"ok": False, "message": str(e), "rows": []}
        finally:
            cursor.close()

    def make_loan_payment(self, customer_id, loan_id, amount):
        cursor = self.conn.cursor(dictionary=True)
        try:
            try:
                 loan_id = int(str(loan_id).strip())
                 amount = float(str(amount).replace(",", ""))
            except ValueError:
                return {"ok": False, "message": "Enter valid numbers for loan ID and payment amount."}

            if amount <= 0:
                return {"ok": False, "message": "Payment amount must be positive."}

            cursor.execute("""
                SELECT loan_id, customer_id, remaining_balance, status
                FROM Loan
                WHERE loan_id = %s
            """, (loan_id,))
            loan = cursor.fetchone()

            if not loan:
                return {"ok": False, "message": "Loan not found."}

            if loan["customer_id"] != customer_id:
                return {"ok": False, "message": "This loan does not belong to you."}

            if loan["status"] not in ("approved", "active"):
                return {"ok": False, "message": f"Cannot make payment on loan with status '{loan['status']}'."}

            remaining_balance = float(loan["remaining_balance"])

            if amount > remaining_balance:
                amount = remaining_balance

            new_balance = round(remaining_balance - amount, 2)
            new_status = "paid_off" if new_balance == 0 else loan["status"]

            cursor.execute("""
                INSERT INTO LoanPayment (loan_id, amount)
                VALUES (%s, %s)
            """, (loan_id, amount))

            cursor.execute("""
                UPDATE Loan
                SET remaining_balance = %s, status = %s
                WHERE loan_id = %s
            """, (new_balance, new_status, loan_id))

            self.conn.commit()

            log_action(
                f"customer:{customer_id}",
                "MAKE_LOAN_PAYMENT",
                f"loan_id={loan_id}, amount={amount}, remaining={new_balance}"
            )

            return {
                "ok": True,
                "message": "Loan payment recorded successfully.",
                "paid_amount": amount,
                "remaining_balance": new_balance,
                "loan_status": new_status
            }

        except Exception as e:
            self.conn.rollback()
            log_error(f"customer:{customer_id}", "MAKE_LOAN_PAYMENT", str(e))
            return {"ok": False, "message": str(e)}
        finally:
            cursor.close()
