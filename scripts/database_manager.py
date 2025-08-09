#!/usr/bin/env python3
"""
数据库管理脚本
用于管理监控地址和查询转账记录
"""

import mysql.connector
import argparse
import sys
from datetime import datetime, timedelta
import json

class DatabaseManager:
    def __init__(self, host='localhost', port=3306, user='root', password='', database='blockchain_monitor'):
        self.config = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'database': database,
            'charset': 'utf8mb4',
            'autocommit': True
        }
    
    def connect(self):
        """连接数据库"""
        try:
            self.conn = mysql.connector.connect(**self.config)
            self.cursor = self.conn.cursor(dictionary=True)
            return True
        except mysql.connector.Error as err:
            print(f"数据库连接失败: {err}")
            return False
    
    def close(self):
        """关闭数据库连接"""
        if hasattr(self, 'cursor'):
            self.cursor.close()
        if hasattr(self, 'conn'):
            self.conn.close()
    
    def add_monitor_address(self, address, token_type, description=""):
        """添加监控地址"""
        try:
            query = """
                INSERT INTO monitor_addresses (address, token_type, description) 
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                token_type = VALUES(token_type),
                description = VALUES(description),
                is_active = TRUE,
                updated_at = CURRENT_TIMESTAMP
            """
            self.cursor.execute(query, (address, token_type, description))
            print(f"成功添加监控地址: {address} ({token_type})")
            return True
        except mysql.connector.Error as err:
            print(f"添加监控地址失败: {err}")
            return False
    
    def remove_monitor_address(self, address):
        """删除监控地址（软删除）"""
        try:
            query = "UPDATE monitor_addresses SET is_active = FALSE WHERE address = %s"
            self.cursor.execute(query, (address,))
            if self.cursor.rowcount > 0:
                print(f"成功删除监控地址: {address}")
                return True
            else:
                print(f"未找到监控地址: {address}")
                return False
        except mysql.connector.Error as err:
            print(f"删除监控地址失败: {err}")
            return False
    
    def list_monitor_addresses(self):
        """列出所有监控地址"""
        try:
            query = "SELECT * FROM monitor_addresses ORDER BY created_at DESC"
            self.cursor.execute(query)
            addresses = self.cursor.fetchall()
            
            if not addresses:
                print("没有找到监控地址")
                return
            
            print("\n监控地址列表:")
            print("-" * 80)
            print(f"{'地址':<42} {'代币类型':<10} {'状态':<8} {'描述':<20}")
            print("-" * 80)
            
            for addr in addresses:
                status = "活跃" if addr['is_active'] else "禁用"
                print(f"{addr['address']:<42} {addr['token_type']:<10} {status:<8} {addr['description']:<20}")
            
            print("-" * 80)
        except mysql.connector.Error as err:
            print(f"查询监控地址失败: {err}")
    
    def get_transfers(self, days=7, token_type=None, transfer_type=None):
        """获取转账记录"""
        try:
            # 构建查询条件
            conditions = ["timestamp >= %s"]
            params = [datetime.now() - timedelta(days=days)]
            
            if token_type:
                conditions.append("token_type = %s")
                params.append(token_type)
            
            if transfer_type == 'incoming':
                conditions.append("to_address IN (SELECT address FROM monitor_addresses WHERE is_active = TRUE)")
            elif transfer_type == 'outgoing':
                conditions.append("from_address IN (SELECT address FROM monitor_addresses WHERE is_active = TRUE)")
            
            where_clause = " AND ".join(conditions)
            query = f"""
                SELECT * FROM token_transfers 
                WHERE {where_clause}
                ORDER BY timestamp DESC 
                LIMIT 100
            """
            
            self.cursor.execute(query, params)
            transfers = self.cursor.fetchall()
            
            if not transfers:
                print("没有找到转账记录")
                return
            
            print(f"\n转账记录 (最近{days}天):")
            print("-" * 120)
            print(f"{'交易哈希':<66} {'代币':<6} {'从':<42} {'到':<42} {'数量':<20} {'时间'}")
            print("-" * 120)
            
            for transfer in transfers:
                timestamp = transfer['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                print(f"{transfer['tx_hash']:<66} {transfer['token_type']:<6} {transfer['from_address']:<42} {transfer['to_address']:<42} {transfer['value']:<20} {timestamp}")
            
            print("-" * 120)
        except mysql.connector.Error as err:
            print(f"查询转账记录失败: {err}")
    
    def get_summary(self, days=30):
        """获取转账统计"""
        try:
            query = """
                SELECT 
                    token_type,
                    COUNT(*) as total_transfers,
                    COUNT(CASE WHEN to_address IN (SELECT address FROM monitor_addresses WHERE is_active = TRUE) THEN 1 END) as incoming_count,
                    COUNT(CASE WHEN from_address IN (SELECT address FROM monitor_addresses WHERE is_active = TRUE) THEN 1 END) as outgoing_count,
                    SUM(CASE WHEN to_address IN (SELECT address FROM monitor_addresses WHERE is_active = TRUE) THEN CAST(value AS DECIMAL(65,0)) ELSE 0 END) as total_incoming_value,
                    SUM(CASE WHEN from_address IN (SELECT address FROM monitor_addresses WHERE is_active = TRUE) THEN CAST(value AS DECIMAL(65,0)) ELSE 0 END) as total_outgoing_value
                FROM token_transfers 
                WHERE timestamp >= %s
                GROUP BY token_type
                ORDER BY token_type
            """
            
            self.cursor.execute(query, (datetime.now() - timedelta(days=days),))
            summary = self.cursor.fetchall()
            
            if not summary:
                print("没有找到转账统计")
                return
            
            print(f"\n转账统计 (最近{days}天):")
            print("-" * 100)
            print(f"{'代币类型':<10} {'总转账数':<10} {'入金数':<8} {'出金数':<8} {'入金总量':<20} {'出金总量':<20}")
            print("-" * 100)
            
            for stat in summary:
                print(f"{stat['token_type']:<10} {stat['total_transfers']:<10} {stat['incoming_count']:<8} {stat['outgoing_count']:<8} {stat['total_incoming_value']:<20} {stat['total_outgoing_value']:<20}")
            
            print("-" * 100)
        except mysql.connector.Error as err:
            print(f"查询转账统计失败: {err}")

def main():
    parser = argparse.ArgumentParser(description='区块链监控数据库管理工具')
    parser.add_argument('--host', default='localhost', help='数据库主机')
    parser.add_argument('--port', type=int, default=3306, help='数据库端口')
    parser.add_argument('--user', default='root', help='数据库用户名')
    parser.add_argument('--password', default='', help='数据库密码')
    parser.add_argument('--database', default='blockchain_monitor', help='数据库名')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 添加监控地址
    add_parser = subparsers.add_parser('add', help='添加监控地址')
    add_parser.add_argument('address', help='钱包地址')
    add_parser.add_argument('token_type', help='代币类型 (ETH/USDT/USDC)')
    add_parser.add_argument('--description', default='', help='描述')
    
    # 删除监控地址
    remove_parser = subparsers.add_parser('remove', help='删除监控地址')
    remove_parser.add_argument('address', help='钱包地址')
    
    # 列出监控地址
    list_parser = subparsers.add_parser('list', help='列出监控地址')
    
    # 查询转账记录
    transfers_parser = subparsers.add_parser('transfers', help='查询转账记录')
    transfers_parser.add_argument('--days', type=int, default=7, help='查询天数')
    transfers_parser.add_argument('--token', help='代币类型过滤')
    transfers_parser.add_argument('--type', choices=['incoming', 'outgoing'], help='转账类型')
    
    # 查询统计
    summary_parser = subparsers.add_parser('summary', help='查询转账统计')
    summary_parser.add_argument('--days', type=int, default=30, help='统计天数')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 创建数据库管理器
    db_manager = DatabaseManager(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        database=args.database
    )
    
    if not db_manager.connect():
        sys.exit(1)
    
    try:
        if args.command == 'add':
            db_manager.add_monitor_address(args.address, args.token_type, args.description)
        elif args.command == 'remove':
            db_manager.remove_monitor_address(args.address)
        elif args.command == 'list':
            db_manager.list_monitor_addresses()
        elif args.command == 'transfers':
            db_manager.get_transfers(args.days, args.token, args.type)
        elif args.command == 'summary':
            db_manager.get_summary(args.days)
    finally:
        db_manager.close()

if __name__ == '__main__':
    main() 