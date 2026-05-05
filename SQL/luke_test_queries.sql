USE banking_system;

SHOW TRIGGERS;

SHOW INDEX FROM Account;
SHOW INDEX FROM `Transaction`;
SHOW INDEX FROM Loan;

SELECT * FROM vw_customer_accounts LIMIT 5;
SELECT * FROM vw_account_transactions LIMIT 5;
SELECT * FROM vw_customer_loans LIMIT 5;

CALL sp_get_customer_accounts(1);
CALL sp_get_account_transactions(1);
CALL sp_get_customer_summary(1);

SELECT loan_id, customer_id, loan_amount, status
FROM Loan
ORDER BY loan_id DESC
LIMIT 5;
