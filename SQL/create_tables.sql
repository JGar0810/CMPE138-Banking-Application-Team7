-- SJSU CMPE 138 SPRING 2026 TEAM7
-- Banking Management System — Table Creation Script

DROP DATABASE IF EXISTS banking_system;
CREATE DATABASE banking_system;
USE banking_system;

CREATE TABLE Branch (
    branch_id       INT             AUTO_INCREMENT PRIMARY KEY,
    branch_name     VARCHAR(100)    NOT NULL,
    location        VARCHAR(255)    NOT NULL,
    phone           VARCHAR(20),
    manager_id      INT             DEFAULT NULL
);

CREATE TABLE Employee (
    employee_id     INT             AUTO_INCREMENT PRIMARY KEY,
    first_name      VARCHAR(50)     NOT NULL,
    last_name       VARCHAR(50)     NOT NULL,
    role            ENUM('teller', 'loan_officer', 'manager') NOT NULL,
    branch_id       INT             NOT NULL,
    email           VARCHAR(100)    NOT NULL UNIQUE,
    login_id        VARCHAR(50)     NOT NULL UNIQUE,
    password_hash   VARCHAR(255)    NOT NULL,
    hire_date       DATE            NOT NULL,
    status          ENUM('active', 'inactive') NOT NULL DEFAULT 'active',

    CONSTRAINT fk_employee_branch
        FOREIGN KEY (branch_id) REFERENCES Branch(branch_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

ALTER TABLE Branch
    ADD CONSTRAINT fk_branch_manager
    FOREIGN KEY (manager_id) REFERENCES Employee(employee_id)
    ON UPDATE CASCADE ON DELETE SET NULL;

CREATE TABLE Customer (
    customer_id         INT             AUTO_INCREMENT PRIMARY KEY,
    first_name          VARCHAR(50)     NOT NULL,
    last_name           VARCHAR(50)     NOT NULL,
    date_of_birth       DATE            NOT NULL,
    address             VARCHAR(255)    NOT NULL,
    phone               VARCHAR(20)     NOT NULL,
    email               VARCHAR(100)    NOT NULL UNIQUE,
    username            VARCHAR(50)     NOT NULL UNIQUE,
    password_hash       VARCHAR(255)    NOT NULL,
    registration_date   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status              ENUM('active', 'inactive', 'suspended') NOT NULL DEFAULT 'active'
);

CREATE TABLE Account (
    account_id      INT             AUTO_INCREMENT PRIMARY KEY,
    customer_id     INT             NOT NULL,
    account_type    ENUM('checking', 'savings') NOT NULL,
    balance         DECIMAL(15, 2)  NOT NULL DEFAULT 0.00,
    date_opened     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status          ENUM('active', 'closed', 'frozen') NOT NULL DEFAULT 'active',

    CONSTRAINT fk_account_customer
        FOREIGN KEY (customer_id) REFERENCES Customer(customer_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE `Transaction` (
    transaction_id      INT             AUTO_INCREMENT PRIMARY KEY,
    account_id          INT             NOT NULL,
    transaction_type    ENUM('deposit', 'withdrawal', 'transfer_in', 'transfer_out') NOT NULL,
    amount              DECIMAL(15, 2)  NOT NULL,
    transaction_date    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    description         VARCHAR(255)    DEFAULT NULL,
    processed_by        INT             DEFAULT NULL,

    CONSTRAINT fk_transaction_account
        FOREIGN KEY (account_id) REFERENCES Account(account_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,

    CONSTRAINT fk_transaction_employee
        FOREIGN KEY (processed_by) REFERENCES Employee(employee_id)
        ON UPDATE CASCADE ON DELETE SET NULL,

    CONSTRAINT chk_transaction_amount
        CHECK (amount > 0)
);

CREATE TABLE Loan (
    loan_id         INT             AUTO_INCREMENT PRIMARY KEY,
    customer_id     INT             NOT NULL,
    loan_amount     DECIMAL(15, 2)  NOT NULL,
    interest_rate   DECIMAL(5, 2)   NOT NULL,
    loan_term_months INT            NOT NULL,
    monthly_payment DECIMAL(15, 2)  NOT NULL,
    remaining_balance DECIMAL(15, 2) NOT NULL,
    status          ENUM('pending', 'approved', 'rejected', 'paid_off') NOT NULL DEFAULT 'pending',
    application_date DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    decision_date   DATETIME        DEFAULT NULL,
    processed_by    INT             DEFAULT NULL,

    CONSTRAINT fk_loan_customer
        FOREIGN KEY (customer_id) REFERENCES Customer(customer_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,

    CONSTRAINT fk_loan_officer
        FOREIGN KEY (processed_by) REFERENCES Employee(employee_id)
        ON UPDATE CASCADE ON DELETE SET NULL,

    CONSTRAINT chk_loan_amount
        CHECK (loan_amount > 0),

    CONSTRAINT chk_interest_rate
        CHECK (interest_rate >= 0)
);

CREATE TABLE Card (
    card_id         INT             AUTO_INCREMENT PRIMARY KEY,
    account_id      INT             NOT NULL,
    card_number     VARCHAR(16)     NOT NULL UNIQUE,
    card_type       ENUM('debit', 'credit') NOT NULL,
    expiry_date     DATE            NOT NULL,
    issue_date      DATE            NOT NULL DEFAULT (CURRENT_DATE),
    status          ENUM('active', 'blocked', 'expired') NOT NULL DEFAULT 'active',

    CONSTRAINT fk_card_account
        FOREIGN KEY (account_id) REFERENCES Account(account_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE LoanPayment (
    payment_id      INT             AUTO_INCREMENT PRIMARY KEY,
    loan_id         INT             NOT NULL,
    amount          DECIMAL(15, 2)  NOT NULL,
    payment_date    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_payment_loan
        FOREIGN KEY (loan_id) REFERENCES Loan(loan_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,

    CONSTRAINT chk_payment_amount
        CHECK (amount > 0)
);
