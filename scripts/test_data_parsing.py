#!/usr/bin/env python3
"""
测试数据解析脚本
用于验证转账数据的解析是否正确
"""

import json
import sys

def test_usdt_parsing():
    """测试USDT数据解析"""
    # 模拟从日志中提取的数据
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
                    "s": "0x6d7d85b5d72b2e22b872937d49e877d9483cbf90d8cabdd6d6d1c3b695507237",
                    "to": "0xdac17f958d2ee523a2206206994597c13d831ec7",
                    "transactionIndex": "0x42",
                    "type": "0x0",
                    "v": "0x25",
                    "value": "0x0"
                }
            }
        }
    }
    
    print("=== 测试USDT数据解析 ===")
    print(f"原始数据: {json.dumps(test_data, indent=2)}")
    
    # 模拟解析过程
    monitor_match = test_data.get('monitor_match', {})
    evm_data = monitor_match.get('EVM', {})
    transaction = evm_data.get('transaction', {})
    matched_on_args = evm_data.get('matched_on_args', {})
    
    print(f"\n解析结果:")
    print(f"交易哈希: {transaction.get('hash', '')}")
    print(f"发送地址: {transaction.get('from', '')}")
    print(f"接收地址: {transaction.get('to', '')}")
    print(f"区块号: {int(transaction.get('blockNumber', '0'), 16)}")
    print(f"Gas使用: {transaction.get('gas', '')}")
    print(f"Gas价格: {transaction.get('gasPrice', '')}")
    
    # 从函数参数中提取转账信息
    transfer_info = {}
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
    
    print(f"\n转账信息:")
    print(f"From: {transfer_info.get('from', '')}")
    print(f"To: {transfer_info.get('to', '')}")
    print(f"Value: {transfer_info.get('value', '0')}")
    
    # 构建最终数据
    final_data = {
        'tx_hash': transaction.get('hash', ''),
        'from': transfer_info.get('from', transaction.get('from', '')),
        'to': transfer_info.get('to', transaction.get('to', '')),
        'value': transfer_info.get('value', transaction.get('value', '0')),
        'token_type': 'USDT',
        'block_number': int(transaction.get('blockNumber', '0'), 16),
        'gas_used': transaction.get('gas', ''),
        'gas_price': transaction.get('gasPrice', ''),
        'status': 'Success'
    }
    
    print(f"\n最终数据:")
    for key, value in final_data.items():
        print(f"{key}: {value}")

def test_usdc_parsing():
    """测试USDC数据解析"""
    # 模拟USDC事件数据
    test_data = {
        "args": ["--verbose"],
        "monitor_match": {
            "EVM": {
                "matched_on_args": {
                    "events": [
                        {
                            "args": [
                                {
                                    "indexed": True,
                                    "kind": "address",
                                    "name": "from",
                                    "value": "0xe0554a476a092703abdb3ef35c80e0d76d32939f"
                                },
                                {
                                    "indexed": True,
                                    "kind": "address",
                                    "name": "to",
                                    "value": "0x51c72848c68a965f66fa7a88855f9f7784502a7f"
                                },
                                {
                                    "indexed": False,
                                    "kind": "uint256",
                                    "name": "value",
                                    "value": "8811030824"
                                }
                            ],
                            "hex_signature": "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
                            "signature": "Transfer(address,address,uint256)"
                        }
                    ]
                },
                "transaction": {
                    "blockHash": "0xe2881c05ed98fba29a8b0a758e11a76b73df3bab5add0672d559fd79e830d20d",
                    "blockNumber": "0x15fe36a",
                    "from": "0x82fab289311422664a26864322bf88eabf5b4131",
                    "gas": "0x25fc3",
                    "gasPrice": "0x1128d2182",
                    "hash": "0x1bf70c4e2425a60686a0eafaeb802cc74cf762f06e44fdbbc21825b74ba30511",
                    "to": "0x51c72848c68a965f66fa7a88855f9f7784502a7f",
                    "value": "0x0"
                }
            }
        }
    }
    
    print("\n=== 测试USDC数据解析 ===")
    
    # 模拟解析过程
    monitor_match = test_data.get('monitor_match', {})
    evm_data = monitor_match.get('EVM', {})
    transaction = evm_data.get('transaction', {})
    matched_on_args = evm_data.get('matched_on_args', {})
    
    # 从事件中提取转账信息
    transfer_info = {}
    events = matched_on_args.get('events', [])
    if events is not None:
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
    
    print(f"\n转账信息:")
    print(f"From: {transfer_info.get('from', '')}")
    print(f"To: {transfer_info.get('to', '')}")
    print(f"Value: {transfer_info.get('value', '0')}")
    
    # 构建最终数据
    final_data = {
        'tx_hash': transaction.get('hash', ''),
        'from': transfer_info.get('from', transaction.get('from', '')),
        'to': transfer_info.get('to', transaction.get('to', '')),
        'value': transfer_info.get('value', transaction.get('value', '0')),
        'token_type': 'USDC',
        'block_number': int(transaction.get('blockNumber', '0'), 16),
        'gas_used': transaction.get('gas', ''),
        'gas_price': transaction.get('gasPrice', ''),
        'status': 'Success'
    }
    
    print(f"\n最终数据:")
    for key, value in final_data.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    test_usdt_parsing()
    test_usdc_parsing() 