USE banking_system;

-- =========================
-- DROP EXISTING OBJECTS
-- =========================

DROP VIEW IF EXISTS vw_customer_accounts;
DROP VIEW IF EXISTS vw_account_transactions;
DROP VIEW IF EXISTS vw_customer_loans;

DROP PROCEDURE IF EXISTS sp_get_customer_accounts;
DROP PROCEDURE IF EXISTS sp_get_account_transactions;
DROP PROCEDURE IF EXISTS sp_get_customer_summary;

DROP TRIGGER IF EXISTS trg_prevent_negative_balance;
DROP TRIGGER IF EXISTS trg_card_expiry_check;

SET @x = (SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'Account' AND index_name = 'idx_account_customer_id');
SET @sql = IF(@x > 0, 'DROP INDEX idx_account_customer_id ON Account', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @x = (SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'Transaction' AND index_name = 'idx_transaction_account_date');
SET @sql = IF(@x > 0, 'DROP INDEX idx_transaction_account_date ON `Transaction`', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @x = (SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'Loan' AND index_name = 'idx_loan_customer_status');
SET @sql = IF(@x > 0, 'DROP INDEX idx_loan_customer_status ON Loan', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
-- =========================
-- VIEWS
-- =========================

CREATE VIEW vw_customer_accounts AS
SELECT
    c.customer_id,
    CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
    c.username,
    a.account_id,
    a.account_type,
    a.balance,
    a.status AS account_status,
    a.date_opened
FROM Customer c
JOIN Account a
    ON c.customer_id = a.customer_id;

CREATE VIEW vw_account_transactions AS
SELECT
    a.account_id,
    CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
    a.account_type,
    t.transaction_id,
    t.transaction_type,
    t.amount,
    t.transaction_date,
    t.description,
    t.processed_by
FROM Account a
JOIN Customer c
    ON a.customer_id = c.customer_id
JOIN `Transaction` t
    ON a.account_id = t.account_id;

CREATE VIEW vw_customer_loans AS
SELECT
    c.customer_id,
    CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
    l.loan_id,
    l.loan_amount,
    l.interest_rate,
    l.loan_term_months,
    l.monthly_payment,
    l.remaining_balance,
    l.status AS loan_status,
    l.application_date,
    l.decision_date
FROM Customer c
JOIN Loan l
    ON c.customer_id = l.customer_id;

-- =========================
-- STORED PROCEDURES
-- =========================

DELIMITER //

CREATE PROCEDURE sp_get_customer_accounts(IN p_customer_id INT)
BEGIN
    SELECT
        a.account_id,
        a.account_type,
        a.balance,
        a.status,
        a.date_opened
    FROM Account a
    WHERE a.customer_id = p_customer_id
    ORDER BY a.account_id;
END //

CREATE PROCEDURE sp_get_account_transactions(IN p_account_id INT)
BEGIN
    SELECT
        t.transaction_id,
        t.transaction_type,
        t.amount,
        t.transaction_date,
        t.description,
        t.processed_by
    FROM `Transaction` t
    WHERE t.account_id = p_account_id
    ORDER BY t.transaction_date DESC, t.transaction_id DESC;
END //

CREATE PROCEDURE sp_get_customer_summary(IN p_customer_id INT)
BEGIN
    SELECT
        c.customer_id,
        CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
        COUNT(DISTINCT a.account_id) AS total_accounts,
        COALESCE(SUM(a.balance), 0) AS total_deposit_balance,
        COUNT(DISTINCT l.loan_id) AS total_loans,
        COALESCE(SUM(
            CASE
                WHEN l.status IN ('approved', 'pending', 'paid_off') THEN l.remaining_balance
                ELSE 0
            END
        ), 0) AS total_remaining_loan_balance
    FROM Customer c
    LEFT JOIN Account a
        ON c.customer_id = a.customer_id
    LEFT JOIN Loan l
        ON c.customer_id = l.customer_id
    WHERE c.customer_id = p_customer_id
    GROUP BY c.customer_id, c.first_name, c.last_name;
END //

CREATE TRIGGER trg_prevent_negative_balance
BEFORE UPDATE ON Account
FOR EACH ROW
BEGIN
    IF NEW.balance < 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Account balance cannot be negative';
    END IF;
END //

CREATE TRIGGER trg_card_expiry_check
BEFORE INSERT ON Card
FOR EACH ROW
BEGIN
    IF NEW.expiry_date <= NEW.issue_date THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Card expiry date must be after issue date';
    END IF;
END //

DELIMITER ;

-- =========================
-- INDEXES
-- =========================

CREATE INDEX idx_account_customer_id
    ON Account(customer_id);

CREATE INDEX idx_transaction_account_date
    ON `Transaction`(account_id, transaction_date);

CREATE INDEX idx_loan_customer_status
    ON Loan(customer_id, status);
