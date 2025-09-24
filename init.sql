-- Initialize POS System Database
-- This script runs when the MySQL container first starts

-- Set character set and collation
ALTER DATABASE pos_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create additional users if needed
-- CREATE USER 'pos_readonly'@'%' IDENTIFIED BY 'readonly_password';
-- GRANT SELECT ON pos_system.* TO 'pos_readonly'@'%';

-- Set MySQL configurations for better performance
SET GLOBAL innodb_buffer_pool_size = 134217728; -- 128MB
SET GLOBAL max_connections = 200;
SET GLOBAL query_cache_size = 33554432; -- 32MB

-- Create logs table for application logging (optional)
-- CREATE TABLE IF NOT EXISTS app_logs (
--     id INT AUTO_INCREMENT PRIMARY KEY,
--     level VARCHAR(20) NOT NULL,
--     message TEXT NOT NULL,
--     module VARCHAR(100),
--     function VARCHAR(100),
--     line_number INT,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     INDEX idx_level (level),
--     INDEX idx_created_at (created_at)
-- );

-- Insert default system settings (will be handled by Flask migrations)
-- These are just examples
-- INSERT IGNORE INTO system_settings (key, value, description) VALUES
-- ('default_currency', 'TSH', 'Default system currency'),
-- ('tax_rate', '0.18', 'Default tax rate'),
-- ('business_name', 'POS System', 'Business name'),
-- ('receipt_footer', 'Thank you for your business!', 'Footer message for receipts');

FLUSH PRIVILEGES;