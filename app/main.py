print("RUNNING FILE:", __file__)
from __future__ import annotations

from app.account_operations import AccountBankingService, OperationResult
from app.card_operations import CardBankingService
from app.db import get_connection


def ask_int(prompt: str, allow_blank: bool = False):
    while True:
        raw = input(prompt).strip()
        if allow_blank and raw == "":
            return None
        try:
            return int(raw)
        except ValueError:
            print("Please enter a whole number.")


def ask_amount(prompt: str, allow_zero: bool = False):
    while True:
        raw = input(prompt).strip()
        try:
            value = float(raw)
            if value < 0 or (not allow_zero and value == 0):
                raise ValueError
            return raw
        except ValueError:
            extra = " or 0" if allow_zero else ""
            print(f"Please enter a positive number{extra}.")


def print_result(result: OperationResult):
    print("\nSUCCESS" if result.ok else "\nERROR")
    print(result.message)
    if result.payload:
        for key, value in result.payload.items():
            print(f"- {key}: {value}")
    print()


def main():
    conn = get_connection()
    account_service = AccountBankingService(conn)
    card_service = CardBankingService(conn)

    try:
        while True:
            print("=" * 56)
            print("Team 7 Banking Management CLI")
            print("1) Open account")
            print("2) Process deposit")
            print("3) Process withdrawal")
            print("4) Close account")
            print("5) Request new card")
            print("6) Report card lost")
            print("7) Transfer funds")
            print("8) Exit")
            choice = input("Choose an option: ").strip()

            if choice == "1":
                customer_id = ask_int("Customer ID: ")
                account_type = input("Account type (checking/savings): ").strip().lower()
                opening_deposit = ask_amount("Opening deposit (0 allowed): ", allow_zero=True)
                teller_id = ask_int("Processing teller employee ID (blank for none): ", allow_blank=True)
                result = account_service.open_account(
                    customer_id=customer_id,
                    account_type=account_type,
                    opening_deposit=opening_deposit,
                    teller_id=teller_id,
                )
                print_result(result)

            elif choice == "2":
                account_id = ask_int("Account ID: ")
                amount = ask_amount("Deposit amount: ")
                teller_id = ask_int("Processing teller employee ID (blank for none): ", allow_blank=True)
                description = input("Description [CLI deposit]: ").strip() or "CLI deposit"
                result = account_service.process_deposit(
                    account_id=account_id,
                    amount=amount,
                    teller_id=teller_id,
                    description=description,
                )
                print_result(result)

            elif choice == "3":
                account_id = ask_int("Account ID: ")
                amount = ask_amount("Withdrawal amount: ")
                teller_id = ask_int("Processing teller employee ID (blank for none): ", allow_blank=True)
                description = input("Description [CLI withdrawal]: ").strip() or "CLI withdrawal"
                result = account_service.process_withdrawal(
                    account_id=account_id,
                    amount=amount,
                    teller_id=teller_id,
                    description=description,
                )
                print_result(result)

            elif choice == "4":
                account_id = ask_int("Account ID: ")
                result = account_service.close_account(account_id=account_id)
                print_result(result)

            elif choice == "5":
                account_id = ask_int("Account ID: ")
                card_type = input("Card type (debit/credit): ").strip().lower()
                employee_id = ask_int("Requesting employee ID (blank for none): ", allow_blank=True)
                result = card_service.request_new_card(
                    account_id=account_id,
                    card_type=card_type,
                    requested_by=employee_id,
                )
                print_result(result)

            elif choice == "6":
                print("Report by one identifier only.")
                card_id = ask_int("Card ID (blank to use card number): ", allow_blank=True)
                card_number = None
                if card_id is None:
                    card_number = input("Card number: ").strip()
                employee_id = ask_int("Reporting employee ID (blank for none): ", allow_blank=True)
                result = card_service.report_card_lost(
                    card_id=card_id,
                    card_number=card_number,
                    reported_by=employee_id,
                )
                print_result(result)

            elif choice == "7":
                from_account_id = ask_int("From account ID: ")
                to_account_id = ask_int("To account ID: ")
                amount = ask_amount("Transfer amount: ")
                employee_id = ask_int("Processing employee ID (blank for none): ", allow_blank=True)

                if not hasattr(account_service, "transfer_funds"):
                    print("\nERROR")
                    print("transfer_funds is not implemented in app/account_operations.py yet.")
                    print("Add the transfer_funds method to AccountBankingService before using this option.\n")
                    continue

                result = account_service.transfer_funds(
                    from_account_id=from_account_id,
                    to_account_id=to_account_id,
                    amount=amount,
                    processed_by=employee_id,
                )
                print_result(result)

            elif choice == "8":
                print("Goodbye.")
                break

            else:
                print("Invalid choice. Please choose 1-8.\n")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
