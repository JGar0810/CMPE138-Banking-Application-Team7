-- SJSU CMPE 138 SPRING 2026 TEAM7
-- Banking Management System — Sample Data
USE banking_system;

INSERT INTO Branch (branch_id, branch_name, location, phone) VALUES
(1, 'Downtown Branch',    '100 Main St, San Jose, CA 95112',      '408-555-0101'),
(2, 'Westside Branch',    '250 Stevens Creek Blvd, San Jose, CA 95128', '408-555-0102'),
(3, 'Eastside Branch',    '500 Capitol Ave, San Jose, CA 95133',  '408-555-0103');

INSERT INTO Employee (employee_id, first_name, last_name, role, branch_id, email, login_id, password_hash, hire_date, status) VALUES
(1, 'Tom',   'Williams', 'manager',      1, 'tom.williams@bank.com',   'mgr_tom',      '$2b$12$mmk0SJXGKnoJLcRfzi0U0.yyy/ySiEMJiYSdNyJZmH2ltbkIPC4WC', '2020-01-15', 'active'),
(2, 'Jane',  'Davis',    'teller',       1, 'jane.davis@bank.com',     'teller_jane',  '$2b$12$zTuXYh0vdMo/NxKUYLuiYuu8m1uGr052uZWr0bh3Ibou/68flHpLi', '2022-06-01', 'active'),
(3, 'Bob',   'Martinez', 'teller',       2, 'bob.martinez@bank.com',   'teller_bob',   '$2b$12$OG2tn7ubaJNQ6bnsNt.qie36laXjtx3PxRBQ0/h.4YcttLRJRKW86', '2023-03-10', 'active'),
(4, 'Sarah', 'Lee',      'loan_officer', 1, 'sarah.lee@bank.com',      'lo_sarah',     '$2b$12$adOeBhUQtDOgvSRSJzvlau/v6ftoaf.RleuPWRKJx8x0YpQae745e', '2021-09-20', 'active');

UPDATE Branch SET manager_id = 1 WHERE branch_id = 1;

INSERT INTO Customer (customer_id, first_name, last_name, date_of_birth, address, phone, email, username, password_hash, registration_date, status) VALUES
(1, 'John',    'Doe',      '1990-05-15', '123 Elm St, San Jose, CA 95112',       '408-555-1001', 'john.doe@email.com',      'jdoe',     '$2b$12$XtaKLowwd7BX6h2/1kR.zOenG0.e.4JMISLZTWxK/QI3W.D8OCdHi', '2024-01-10 09:30:00', 'active'),
(2, 'Alice',   'Smith',    '1985-11-22', '456 Oak Ave, San Jose, CA 95128',      '408-555-1002', 'alice.smith@email.com',   'asmith',   '$2b$12$5EdhT7Lx7WIzgEyRyBrrcenOBWvfIl6pliL8g4bFADpqol88NtonS', '2024-02-20 14:15:00', 'active'),
(3, 'Mike',    'Johnson',  '1995-08-03', '789 Pine Rd, San Jose, CA 95133',      '408-555-1003', 'mike.johnson@email.com',  'mjohnson', '$2b$12$IIU2Nr4a0Ne660.OEJDlVO4y92Sffa7nyXPMZPNSvUSBzSoZbrc0q', '2024-03-05 10:00:00', 'active');

INSERT INTO Account (account_id, customer_id, account_type, balance, date_opened, status) VALUES
(1, 1, 'checking', 5200.00,  '2024-01-10 09:35:00', 'active'),
(2, 1, 'savings',  12000.00, '2024-01-10 09:40:00', 'active'),
(3, 2, 'checking', 3400.50,  '2024-02-20 14:20:00', 'active'),
(4, 2, 'savings',  25000.00, '2024-02-20 14:25:00', 'active'),
(5, 3, 'checking', 800.75,   '2024-03-05 10:05:00', 'active');

INSERT INTO `Transaction` (transaction_id, account_id, transaction_type, amount, transaction_date, description, processed_by) VALUES
(1,  1, 'deposit',      2000.00, '2024-01-15 10:00:00', 'Initial deposit',           2),
(2,  1, 'deposit',      3500.00, '2024-02-01 11:30:00', 'Payroll direct deposit',    NULL),
(3,  1, 'withdrawal',    300.00, '2024-02-05 14:00:00', 'ATM withdrawal',            NULL),
(4,  1, 'transfer_out', 1000.00, '2024-02-10 09:00:00', 'Transfer to savings',       NULL),
(5,  2, 'transfer_in',  1000.00, '2024-02-10 09:00:00', 'Transfer from checking',    NULL),
(6,  3, 'deposit',      5000.00, '2024-02-21 09:00:00', 'Initial deposit',           2),
(7,  3, 'withdrawal',    500.00, '2024-03-01 16:00:00', 'Bill payment',              NULL),
(8,  3, 'deposit',      1200.00, '2024-03-15 12:00:00', 'Freelance payment',         NULL),
(9,  4, 'deposit',     20000.00, '2024-02-22 10:00:00', 'Savings deposit',           3),
(10, 5, 'deposit',      1000.00, '2024-03-06 09:30:00', 'Initial deposit',           2),
(11, 5, 'withdrawal',    200.00, '2024-03-20 15:00:00', 'Grocery shopping',          NULL);

INSERT INTO Loan (loan_id, customer_id, loan_amount, interest_rate, loan_term_months, monthly_payment, remaining_balance, status, application_date, decision_date, processed_by) VALUES
(1, 1, 10000.00, 5.50, 36, 301.96, 8750.00,  'approved', '2024-02-15 10:00:00', '2024-02-18 14:00:00', 4),
(2, 2, 25000.00, 4.25, 60, 463.12, 25000.00, 'approved', '2024-03-01 11:00:00', '2024-03-05 09:30:00', 4),
(3, 3,  5000.00, 6.00, 24, 221.60,  5000.00, 'pending',  '2024-03-25 14:00:00',  NULL,                 NULL);

INSERT INTO LoanPayment (payment_id, loan_id, amount, payment_date) VALUES
(1, 1, 301.96, '2024-03-15 10:00:00'),
(2, 1, 301.96, '2024-04-15 10:00:00'),
(3, 1, 301.96, '2024-05-15 10:00:00'),
(4, 1, 301.96, '2024-06-15 10:00:00');

INSERT INTO Card (card_id, account_id, card_number, card_type, expiry_date, issue_date, status) VALUES
(1, 1, '4111111111111111', 'debit',  '2027-01-31', '2024-01-10', 'active'),
(2, 1, '5222222222222222', 'credit', '2027-06-30', '2024-03-01', 'active'),
(3, 3, '4333333333333333', 'debit',  '2027-02-28', '2024-02-20', 'active'),
(4, 5, '4444444444444444', 'debit',  '2027-03-31', '2024-03-05', 'blocked');
