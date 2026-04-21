USE banking_system;
SHOW TABLES;

SELECT * FROM vw_customer_accounts;
SELECT * FROM vw_account_transactions;
SELECT * FROM vw_customer_loans;

CALL sp_get_customer_accounts(1);
CALL sp_get_account_transactions(1);
CALL sp_get_customer_summary(1);

SHOW INDEX FROM Account;
SHOW INDEX FROM `Transaction`;
SHOW INDEX FROM Loan;

SHOW TRIGGERS;