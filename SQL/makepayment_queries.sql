-- 5) Make Payment demo (Person 5)

-- Before payment: show current remaining balance and payments
SELECT loan_id, customer_id, loan_amount, remaining_balance, status
FROM Loan
WHERE loan_id = 1;

SELECT *
FROM LoanPayment
WHERE loan_id = 1
ORDER BY payment_id DESC;

-- Simulate making a new payment of 301.96 on loan 1
START TRANSACTION;

INSERT INTO LoanPayment (loan_id, amount, payment_date)
VALUES (1, 301.96, NOW());

UPDATE Loan
SET remaining_balance = remaining_balance - 301.96
WHERE loan_id = 1;

COMMIT;

-- After payment: verify new payment row and updated remaining balance
SELECT loan_id, customer_id, loan_amount, remaining_balance, status
FROM Loan
WHERE loan_id = 1;

SELECT *
FROM LoanPayment
WHERE loan_id = 1
ORDER BY payment_id DESC;
