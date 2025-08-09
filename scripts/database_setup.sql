-- 创建数据库
CREATE DATABASE IF NOT EXISTS blockchain_monitor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE blockchain_monitor;

-- 创建监控地址表
CREATE TABLE IF NOT EXISTS monitor_addresses (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    address VARCHAR(42) NOT NULL UNIQUE,
    token_type VARCHAR(10) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_address (address),
    INDEX idx_token_type (token_type),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建转账记录表
CREATE TABLE IF NOT EXISTS token_transfers (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tx_hash VARCHAR(66) NOT NULL,
    from_address VARCHAR(42) NOT NULL,
    to_address VARCHAR(42) NOT NULL,
    value VARCHAR(255) NOT NULL,
    token_type VARCHAR(10) NOT NULL,
    block_number BIGINT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    gas_used VARCHAR(255),
    gas_price VARCHAR(255),
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_tx_hash (tx_hash),
    INDEX idx_from_address (from_address),
    INDEX idx_to_address (to_address),
    INDEX idx_token_type (token_type),
    INDEX idx_block_number (block_number),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入默认监控地址
INSERT IGNORE INTO monitor_addresses (address, token_type, description) VALUES
('0x0000000000000000000000000000000000000000', 'ETH', 'ETH主币转账监控'),
('0xdAC17F958D2ee523a2206206994597C13D831ec7', 'USDT', 'USDT代币转账监控'),
('0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48', 'USDC', 'USDC代币转账监控');

-- 创建视图：入金记录
CREATE OR REPLACE VIEW incoming_transfers AS
SELECT 
    id,
    tx_hash,
    from_address,
    to_address,
    value,
    token_type,
    block_number,
    timestamp,
    gas_used,
    gas_price,
    status,
    created_at,
    'INCOMING' as transfer_type
FROM token_transfers 
WHERE to_address IN (SELECT address FROM monitor_addresses WHERE is_active = TRUE);

-- 创建视图：出金记录
CREATE OR REPLACE VIEW outgoing_transfers AS
SELECT 
    id,
    tx_hash,
    from_address,
    to_address,
    value,
    token_type,
    block_number,
    timestamp,
    gas_used,
    gas_price,
    status,
    created_at,
    'OUTGOING' as transfer_type
FROM token_transfers 
WHERE from_address IN (SELECT address FROM monitor_addresses WHERE is_active = TRUE);

-- 创建统计视图
CREATE OR REPLACE VIEW transfer_summary AS
SELECT 
    token_type,
    DATE(timestamp) as transfer_date,
    COUNT(*) as total_transfers,
    COUNT(CASE WHEN to_address IN (SELECT address FROM monitor_addresses WHERE is_active = TRUE) THEN 1 END) as incoming_count,
    COUNT(CASE WHEN from_address IN (SELECT address FROM monitor_addresses WHERE is_active = TRUE) THEN 1 END) as outgoing_count,
    SUM(CASE WHEN to_address IN (SELECT address FROM monitor_addresses WHERE is_active = TRUE) THEN CAST(value AS DECIMAL(65,0)) ELSE 0 END) as total_incoming_value,
    SUM(CASE WHEN from_address IN (SELECT address FROM monitor_addresses WHERE is_active = TRUE) THEN CAST(value AS DECIMAL(65,0)) ELSE 0 END) as total_outgoing_value
FROM token_transfers 
WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY token_type, DATE(timestamp)
ORDER BY token_type, transfer_date DESC; 