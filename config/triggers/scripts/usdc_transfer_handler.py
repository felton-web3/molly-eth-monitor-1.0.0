#!/Users/user/Code/openzeppelin-monitor-1.0.0/venv/bin/python
"""
USDC转账处理器
处理USDC代币转账数据并存储到MySQL数据库
"""

import json
import sys
import os
import time
import mysql.connector
from datetime import datetime
import argparse
import logging
from pathlib import Path

def setup_logging():
    """设置日志配置"""
    # 创建日志目录
    log_dir = Path("/Users/user/dumps")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成日志文件名（包含今天日期）
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = log_dir / f"usdc-{today}.log"
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            # logging.StreamHandler(sys.stderr)  # 同时输出到控制台
        ]
    )
    
    return logging.getLogger(__name__)

def get_env(key, default_value):
    """获取环境变量"""
    return os.getenv(key, default_value)

def connect_database():
    """连接数据库"""
    logger = logging.getLogger(__name__)
    db_host = get_env("DB_HOST", "localhost")
    db_port = int(get_env("DB_PORT", "3306"))
    db_user = get_env("DB_USER", "root")
    db_password = get_env("DB_PASSWORD", "windows")
    db_name = get_env("DB_NAME", "blockchain_monitor")
    
    try:
        conn = mysql.connector.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name,
            charset='utf8mb4',
            autocommit=True,
            pool_size=5,
            pool_name="monitor_pool",
            pool_reset_session=True
        )
        logger.info(f"成功连接到数据库: {db_host}:{db_port}/{db_name}")
        return conn
    except mysql.connector.Error as err:
        logger.error(f"数据库连接失败: {err}")
        return None

def create_table_if_not_exists(conn):
    """创建表（如果不存在）"""
    logger = logging.getLogger(__name__)
    cursor = conn.cursor()
    
    query = """
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
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """
    
    try:
        cursor.execute(query)
        conn.commit()
        logger.info("成功创建或确认token_transfers表存在")
        return True
    except mysql.connector.Error as err:
        logger.error(f"创建表失败: {err}")
        return False

def save_transfer_data(conn, transfer_data, verbose=False):
    """保存转账数据到数据库"""
    logger = logging.getLogger(__name__)
    cursor = conn.cursor()
    
    query = """
    INSERT INTO token_transfers 
    (tx_hash, from_address, to_address, value, token_type, block_number, timestamp, gas_used, gas_price, status, created_at) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    try:
        cursor.execute(query, (
            transfer_data['tx_hash'],
            transfer_data['from'],
            transfer_data['to'],
            transfer_data['value'],
            transfer_data['token_type'],
            transfer_data['block_number'],
            datetime.now(),  # 使用当前时间
            transfer_data['gas_used'],
            transfer_data['gas_price'],
            transfer_data['status'],
            datetime.now()
        ))
        conn.commit()
        
        if verbose:
            logger.info(f"成功插入USDC转账记录: {transfer_data['tx_hash']}")
        else:
            logger.info(f"成功插入USDC转账记录: {transfer_data['tx_hash']}")
        
        return True
    except mysql.connector.Error as err:
        logger.error(f"插入数据失败: {err}")
        return False

def process_usdc_transfer(input_data, verbose=False):
    """处理USDC转账数据"""
    logger = logging.getLogger(__name__)
    try:
        # 解析输入数据
        if isinstance(input_data, str):
            data = json.loads(input_data)
        else:
            data = input_data
        
        # 检查是否为详细模式
        args = data.get('args', [])
        if '--verbose' in args:
            verbose = True
        
        if verbose:
            logger.info(f"收到USDC转账数据: {json.dumps(data, indent=2)}")
            logger.info("数据结构分析:")
            logger.info(f"  monitor_match键: {list(data.get('monitor_match', {}).keys())}")
            logger.info(f"  EVM键: {list(data.get('monitor_match', {}).get('EVM', {}).keys())}")
            logger.info(f"  transaction键: {list(data.get('monitor_match', {}).get('EVM', {}).get('transaction', {}).keys())}")
            logger.info(f"  matched_on_args键: {list(data.get('monitor_match', {}).get('EVM', {}).get('matched_on_args', {}).keys())}")
        
        # 提取监控匹配数据
        monitor_match = data.get('monitor_match', {})
        evm_data = monitor_match.get('EVM', {})
        transaction = evm_data.get('transaction', {})
        matched_on_args = evm_data.get('matched_on_args', {})
        
        # 从事件中提取转账信息
        transfer_info = {}
        events = matched_on_args.get('events', [])
        if events is not None:  # 确保events不是None
            for event in events:
                if event.get('signature') == 'Transfer(address,address,uint256)':
                    args = event.get('args', [])
                    for arg in args:
                        if arg.get('name') == 'from':
                            transfer_info['from'] = arg.get('value', '')
                        elif arg.get('name') == 'to':
                            transfer_info['to'] = arg.get('value', '')
                        elif arg.get('name') == 'value':
                            transfer_info['value'] = arg.get('value', '0')
                    break
        
        # 如果没有找到事件数据，尝试从函数参数中提取
        if not transfer_info:
            functions = matched_on_args.get('functions', [])
            if functions is not None:
                for func in functions:
                    if func.get('signature') == 'transfer(address,uint256)':
                        args = func.get('args', [])
                        for arg in args:
                            if arg.get('name') == 'to':
                                transfer_info['to'] = arg.get('value', '')
                            elif arg.get('name') == 'value':
                                transfer_info['value'] = arg.get('value', '0')
                        # 对于函数调用，from地址就是交易的from地址
                        transfer_info['from'] = transaction.get('from', '')
                        break
        
        # 构建转账数据
        transfer_data = {
            'tx_hash': transaction.get('hash', ''),
            'from': transfer_info.get('from', transaction.get('from', '')),
            'to': transfer_info.get('to', transaction.get('to', '')),
            'value': transfer_info.get('value', transaction.get('value', '0')),
            'token_type': 'USDC',
            'block_number': int(transaction.get('blockNumber', '0'), 16) if isinstance(transaction.get('blockNumber', '0'), str) else transaction.get('block_number', 0),
            'timestamp': int(time.time()),  # 使用当前时间
            'gas_used': transaction.get('gas', ''),
            'gas_price': transaction.get('gasPrice', ''),
            'status': 'Success'  # 默认成功状态
        }
        
        logger.info(f"数据记录: {transfer_data}")
        
        # 验证数据完整性
        if not transfer_data['tx_hash'] or not transfer_data['from'] or not transfer_data['to'] or transfer_data['block_number'] == 0:
            if verbose:
                logger.warning(f"数据不完整，跳过插入: {transfer_data}")
            return False
        
        # 连接数据库
        conn = connect_database()
        if not conn:
            return False
        
        try:
            # 创建表（如果不存在）
            if not create_table_if_not_exists(conn):
                return False
            
            # 保存数据
            if not save_transfer_data(conn, transfer_data, verbose):
                return False
            
            if verbose:
                logger.info("USDC转账数据已成功保存到数据库")
            
            return True
            
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"处理USDC转账数据失败: {e}")
        return False

def main():
    """主函数"""
    # 设置日志
    logger = setup_logging()
    
    # 从标准输入读取JSON数据
    try:
        input_json = sys.stdin.read()
        if not input_json.strip():
            logger.error("没有输入数据")
            sys.exit(1)
        
        # 解析JSON数据
        input_data = json.loads(input_json)
        
        # 处理USDC转账
        if process_usdc_transfer(input_data):
            logger.info("USDC转账处理完成")
            sys.exit(0)
        else:
            logger.error("USDC转账处理失败")
            sys.exit(1)
            
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"处理失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 