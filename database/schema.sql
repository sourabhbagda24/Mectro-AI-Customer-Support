-- Mectro AI Customer Support System
-- Database schema
-- Run with: mysql -u root -p < database/schema.sql

CREATE DATABASE IF NOT EXISTS mectro_support
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE mectro_support;

-- ---------------------------------------------------------------
-- policies: static policy text the SQL agent looks up
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS policies (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    policy_type VARCHAR(50)  NOT NULL UNIQUE,
    title       VARCHAR(150) NOT NULL,
    content     TEXT         NOT NULL,
    updated_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
                             ON UPDATE CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------
-- orders: sample order records the SQL agent looks up
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS orders (
    id                 INT AUTO_INCREMENT PRIMARY KEY,
    order_id           VARCHAR(20)    NOT NULL UNIQUE,
    customer_name      VARCHAR(100)   NOT NULL,
    order_status       VARCHAR(50)    NOT NULL,
    payment_status     VARCHAR(50)    NOT NULL,
    tracking_number    VARCHAR(50)    NULL,
    carrier            VARCHAR(50)    NULL,
    expected_delivery  DATE           NULL,
    order_amount       DECIMAL(10,2)  NOT NULL,
    created_at         TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------
-- support_logs: audit trail written after every pipeline run
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS support_logs (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    customer_query  TEXT        NOT NULL,
    detected_intent VARCHAR(50) NOT NULL,
    order_id        VARCHAR(20) NULL,
    retrieved_data  TEXT        NULL,
    final_response  TEXT        NULL,
    created_at      TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP
);
