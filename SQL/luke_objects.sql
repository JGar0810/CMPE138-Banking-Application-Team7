USE bankingsystem;

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

SET @x = (
    SELECT COUNT(*)
    FROM information_schema.statistics
    WHERE table_schema = DATABASE()
      AND table_name = 'Account'
      AND index_name = 'idx_account_customerid'
);
SET @sql = IF(@x > 0, 'DROP INDEX idx_account_customerid ON Account', 'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @x = (
    SELECT COUNT(*)
    FROM information_schema.statistics
    WHERE table_schema = DATABASE()
      AND table_name = 'Transaction'
      AND index_name = 'idx_transaction_accountid_date'
);
SET @sql = IF(@x > 0, 'DROP INDEX idx_transaction_accountid_date ON `Transaction`', 'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @x = (
    SELECT COUNT(*)
    FROM information_schema.statistics
    WHERE table_schema = DATABASE()
      AND table_name = 'Loan'
      AND index_name = 'idx_loan_customerid_status'
);
SET @sql = IF(@x > 0, 'DROP INDEX idx_loan_customerid_status ON Loan', 'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- =========================
-- VIEWS
-- =========================

CREATE VIEW vw_customer_accounts AS
SELECT
    c.customerid,
    CONCAT(c.firstname, ' ', c.lastname) AS customername,
    c.username,
    a.accountid,
    a.accounttype,
    a.balance,
    a.status AS accountstatus,
    a.dateopened
FROM Customer c
JOIN Account a
    ON c.customerid = a.customerid;

CREATE VIEW vw_account_transactions AS
SELECT
    a.accountid,
    CONCAT(c.firstname, ' ', c.lastname) AS customername,
    a.accounttype,
    t.transactionid,
    t.transactiontype,
    t.amount,
    t.transactiondate,
    t.description,
    t.processedby
FROM Account a
JOIN Customer c
    ON a.customerid = c.customerid
JOIN `Transaction` t
    ON a.accountid = t.accountid;

CREATE VIEW vw_customer_loans AS
SELECT
    c.customerid,
    CONCAT(c.firstname, ' ', c.lastname) AS customername,
    l.loanid,
    l.loanamount,
    l.interestrate,
    l.loantermmonths,
    l.monthlypayment,
    l.remainingbalance,
    l.status AS loanstatus,
    l.applicationdate,
    l.decisiondate
FROM Customer c
JOIN Loan l
    ON c.customerid = l.customerid;

-- =========================
-- STORED PROCEDURES
-- =========================

DELIMITER //

CREATE PROCEDURE sp_get_customer_accounts(IN p_customerid INT)
BEGIN
    SELECT
        a.accountid,
        a.accounttype,
        a.balance,
        a.status,
        a.dateopened
    FROM Account a
    WHERE a.customerid = p_customerid
    ORDER BY a.accountid;
END //

CREATE PROCEDURE sp_get_account_transactions(IN p_accountid INT)
BEGIN
    SELECT
        t.transactionid,
        t.transactiontype,
        t.amount,
        t.transactiondate,
        t.description,
        t.processedby
    FROM `Transaction` t
    WHERE t.accountid = p_accountid
    ORDER BY t.transactiondate DESC, t.transactionid DESC;
END //

CREATE PROCEDURE sp_get_customer_summary(IN p_customerid INT)
BEGIN
    SELECT
        c.customerid,
        CONCAT(c.firstname, ' ', c.lastname) AS customername,
        COUNT(DISTINCT a.accountid) AS totalaccounts,
        COALESCE(SUM(a.balance), 0) AS totaldepositbalance,
        COUNT(DISTINCT l.loanid) AS totalloans,
        COALESCE(SUM(
            CASE
                WHEN l.status IN ('approved', 'pending', 'paidoff') THEN l.remainingbalance
                ELSE 0
            END
        ), 0) AS totalremainingloanbalance
    FROM Customer c
    LEFT JOIN Account a
        ON c.customerid = a.customerid
    LEFT JOIN Loan l
        ON c.customerid = l.customerid
    WHERE c.customerid = p_customerid
    GROUP BY c.customerid, c.firstname, c.lastname;
END //

-- =========================
-- TRIGGERS
-- =========================

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
    IF NEW.expirydate <= NEW.issuedate THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Card expiry date must be after issue date';
    END IF;
END //

DELIMITER ;

-- =========================
-- INDEXES
-- =========================

CREATE INDEX idx_account_customerid
ON Account(customerid);

CREATE INDEX idx_transaction_accountid_date
ON `Transaction`(accountid, transactiondate);

CREATE INDEX idx_loan_customerid_status
ON Loan(customerid, status);
