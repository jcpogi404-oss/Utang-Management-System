-- Create database
CREATE DATABASE IF NOT EXISTS store_credit_system;
USE store_credit_system;

-- Create credits table
CREATE TABLE IF NOT EXISTS credits (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_name VARCHAR(255) NOT NULL,
    product VARCHAR(255) NOT NULL,
    cost DECIMAL(10, 2) NOT NULL,
    estimated_payment_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending', 'paid') DEFAULT 'pending',
    paid_date TIMESTAMP NULL
);

-- Create index for better performance
CREATE INDEX idx_customer_name ON credits(customer_name);
CREATE INDEX idx_status ON credits(status);
CREATE INDEX idx_payment_date ON credits(estimated_payment_date);
