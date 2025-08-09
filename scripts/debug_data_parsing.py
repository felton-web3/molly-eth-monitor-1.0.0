#!/usr/bin/env python3
"""
调试数据解析脚本
用于分析转账数据的实际结构
"""

import json
import sys
import os

def analyze_data_structure(data):
    """分析数据结构"""
    print("=== 数据结构分析 ===")
    
    # 检查顶层结构
    print(f"顶层键: {list(data.keys())}")
    
    # 检查monitor_match结构
    monitor_match = data.get('monitor_match', {})
    print(f"monitor_match键: {list(monitor_match.keys())}")
    
    # 检查EVM结构
    evm_data = monitor_match.get('EVM', {})
    print(f"EVM键: {list(evm_data.keys())}")
    
    # 检查transaction结构
    transaction = evm_data.get('transaction', {})
    print(f"transaction键: {list(transaction.keys())}")
    print(f"transaction.hash: {transaction.get('hash', 'NOT_FOUND')}")
    print(f"transaction.from: {transaction.get('from', 'NOT_FOUND')}")
    print(f"transaction.to: {transaction.get('to', 'NOT_FOUND')}")
    print(f"transaction.blockNumber: {transaction.get('blockNumber', 'NOT_FOUND')}")
    print(f"transaction.value: {transaction.get('value', 'NOT_FOUND')}")
    
    # 检查matched_on_args结构
    matched_on_args = evm_data.get('matched_on_args', {})
    print(f"matched_on_args键: {list(matched_on_args.keys())}")
    
    # 检查events
    events = matched_on_args.get('events', [])
    print(f"events类型: {type(events)}, 值: {events}")
    if events and isinstance(events, list):
        for i, event in enumerate(events):
            print(f"事件{i}: {event}")
    
    # 检查functions
    functions = matched_on_args.get('functions', [])
    print(f"functions类型: {type(functions)}, 值: {functions}")
    if functions and isinstance(functions, list):
        for i, func in enumerate(functions):
            print(f"函数{i}: {func}")
    
    return {
        'transaction': transaction,
        'events': events,
        'functions': functions
    }

def test_usdt_parsing():
    """测试USDT数据解析"""
    print("\n=== 测试USDT数据解析 ===")
    
    # 模拟USDT函数调用数据
    test_data = {
        "args": ["--verbose"],
        "monitor_match": {
            "EVM": {
                "logs": [],
                "matched_on": {
                    "events": [],
                    "functions": [
                        {
                            "expression": None,
                            "signature": "transfer(address,uint256)"
                        }
                    ],
                    "transactions": [
                        {
                            "expression": None,
                            "status": "Success"
                        }
                    ]
                },
                "matched_on_args": {
                    "events": None,
                    "functions": [
                        {
                            "args": [
                                {
                                    "indexed": False,
                                    "kind": "address",
                                    "name": "to",
                                    "value": "0xcffad3200574698b78f32232aa9d63eabd290703"
                                },
                                {
                                    "indexed": False,
                                    "kind": "uint256",
                                    "name": "value",
                                    "value": "1735422411"
                                }
                            ],
                            "hex_signature": "a9059cbb",
                            "signature": "transfer(address,uint256)"
                        }
                    ]
                },
                "transaction": {
                    "blockHash": "0x557f979ba7bf5a108c809df8933fc7ba42ba93d7a0a63b6f94ec65727317514d",
                    "blockNumber": "0x15fe3c4",
                    "chainId": "0x1",
                    "from": "0x58a4d6b6f50b3e49a2af4a17f6d7c5b2d83c8201",
                    "gas": "0x13880",
                    "gasPrice": "0x77359400",
                    "hash": "0xb8ee1f267aff8064c7c864ecbfe580ffd93302a6a48700fc3ec2f32695cef21a",
                    "input": "0xa9059cbb000000000000000000000000cffad3200574698b78f32232aa9d63eabd29070300000000000000000000000000000000000000000000000000000000677071cb",
                    "nonce": "0x219f",
                    "r": "0xf519829edc912c3611b7a2ed8d0ea622acc2b98fa43cd218a538f109589f2865",
                    "s": "0x46bc6ae887692462ec9915c58efa4f924f71ba0e7bacdd337a409f296146b020",
                    "to": "0xdac17f958d2ee523a2206206994597c13d831ec7",
                    "transactionIndex": "0x42",
                    "type": "0x0",
                    "v": "0x25",
                    "value": "0x0"
                }
            }
        }
    }
    
    # 分析数据结构
    parsed = analyze_data_structure(test_data)
    
    # 模拟解析过程
    print("\n=== 解析过程 ===")
    
    # 提取数据
    transaction = parsed['transaction']
    functions = parsed['functions']
    
    # 从函数参数中提取转账信息
    transfer_info = {}
    if functions and isinstance(functions, list):
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
    
    print(f"提取的转账信息: {transfer_info}")
    
    # 构建最终数据
    final_data = {
        'tx_hash': transaction.get('hash', ''),
        'from': transfer_info.get('from', transaction.get('from', '')),
        'to': transfer_info.get('to', transaction.get('to', '')),
        'value': transfer_info.get('value', transaction.get('value', '0')),
        'token_type': 'USDT',
        'block_number': int(transaction.get('blockNumber', '0'), 16) if isinstance(transaction.get('blockNumber', '0'), str) else transaction.get('block_number', 0),
        'gas_used': transaction.get('gas', ''),
        'gas_price': transaction.get('gasPrice', ''),
        'status': 'Success'
    }
    
    print(f"\n最终数据:")
    for key, value in final_data.items():
        print(f"{key}: {value}")
    
    # 验证数据完整性
    is_valid = (final_data['tx_hash'] and 
                final_data['from'] and 
                final_data['to'] and 
                final_data['block_number'] > 0)
    
    print(f"\n数据完整性检查: {'通过' if is_valid else '失败'}")

def test_eth_parsing():
    """测试ETH数据解析"""
    print("\n=== 测试ETH数据解析 ===")
    
    # 模拟ETH转账数据
    test_data = {
        "args": ["--verbose"],
        "monitor_match": {
            "EVM": {
                "transaction": {
                    "blockHash": "0x1234567890abcdef",
                    "blockNumber": "0x15fe3c5",
                    "from": "0x1234567890123456789012345678901234567890",
                    "gas": "0x186a0",
                    "gasPrice": "0x77359400",
                    "hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
                    "to": "0x9876543210987654321098765432109876543210",
                    "value": "0xde0b6b3a7640000"  # 1 ETH in wei
                }
            }
        }
    }
    
    # 分析数据结构
    parsed = analyze_data_structure(test_data)
    
    # 模拟解析过程
    print("\n=== 解析过程 ===")
    
    transaction = parsed['transaction']
    
    # 构建最终数据
    final_data = {
        'tx_hash': transaction.get('hash', ''),
        'from': transaction.get('from', ''),
        'to': transaction.get('to', ''),
        'value': transaction.get('value', '0'),
        'token_type': 'ETH',
        'block_number': int(transaction.get('blockNumber', '0'), 16) if isinstance(transaction.get('blockNumber', '0'), str) else transaction.get('block_number', 0),
        'gas_used': transaction.get('gas', ''),
        'gas_price': transaction.get('gasPrice', ''),
        'status': 'Success'
    }
    
    print(f"\n最终数据:")
    for key, value in final_data.items():
        print(f"{key}: {value}")
    
    # 验证数据完整性
    is_valid = (final_data['tx_hash'] and 
                final_data['from'] and 
                final_data['to'] and 
                final_data['block_number'] > 0)
    
    print(f"\n数据完整性检查: {'通过' if is_valid else '失败'}")

if __name__ == "__main__":
    test_usdt_parsing()
    test_eth_parsing() 