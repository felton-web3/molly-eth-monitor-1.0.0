# ETH链监控系统

这是一个基于OpenZeppelin Monitor的ETH链监控系统，用于监控ETH主币、USDT和USDC代币的转账活动，并将数据存储到MySQL数据库中。

## 功能特性

- ✅ 监控ETH主币转账
- ✅ 监控USDT代币转账
- ✅ 监控USDC代币转账
- ✅ MySQL数据库存储
- ✅ 动态添加/删除监控地址
- ✅ 入金/出金状态跟踪
- ✅ Go语言触发器脚本
- ✅ 实时数据统计

## 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   ETH区块链     │    │  OpenZeppelin   │    │   MySQL数据库   │
│                 │◄──►│     Monitor     │◄──►│                 │
│   - ETH主币     │    │                 │    │   - 转账记录    │
│   - USDT代币    │    │   - 区块监控    │    │   - 监控地址    │
│   - USDC代币    │    │   - 事件过滤    │    │   - 统计视图    │
└─────────────────┘    │   - 触发器      │    └─────────────────┘
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Go触发器脚本   │
                       │                 │
                       │   - 数据处理    │
                       │   - 数据库存储  │
                       └─────────────────┘
```

## 快速开始

### 1. 环境准备

确保您的系统已安装以下依赖：

- Rust (1.84+)
- Go (1.21+)
- MySQL (8.0+)
- Python3 (可选，用于数据库管理)

### 2. 配置环境

复制环境变量文件并修改配置：

```bash
cp env.example .env
```

编辑 `.env` 文件，设置数据库连接信息：

```bash
# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=blockchain_monitor
```

### 3. 初始化系统

```bash
# 给启动脚本执行权限
chmod +x scripts/start_monitor.sh

# 初始化数据库
./scripts/start_monitor.sh init

# 编译Go脚本
./scripts/start_monitor.sh compile
```

### 4. 启动监控

```bash
# 启动监控服务
./scripts/start_monitor.sh start

# 查看状态
./scripts/start_monitor.sh status
```

## 配置文件说明

### 网络配置 (`config/networks/ethereum_mainnet.json`)

```json
{
  "network_type": "EVM",
  "slug": "ethereum_mainnet",
  "name": "Ethereum Mainnet",
  "rpc_urls": [
    {
      "type_": "rpc",
      "url": {
        "type": "plain",
        "value": "https://eth.drpc.org"
      },
      "weight": 100
    }
  ],
  "chain_id": 1,
  "block_time_ms": 12000,
  "confirmation_blocks": 12,
  "cron_schedule": "0 */1 * * * *",
  "max_past_blocks": 18,
  "store_blocks": false
}
```

### 监控配置

系统包含三个监控配置：

1. **ETH主币监控** (`config/monitors/eth_transfer_monitor.json`)
2. **USDT代币监控** (`config/monitors/usdt_transfer_monitor.json`)
3. **USDC代币监控** (`config/monitors/usdc_transfer_monitor.json`)

### 触发器配置 (`config/triggers/database_notifications.json`)

```json
{
  "eth_transfer_database": {
    "name": "ETH Transfer Database Handler",
    "trigger_type": "script",
    "config": {
      "language": "Go",
      "script_path": "./config/triggers/scripts/eth_transfer_handler.go",
      "arguments": ["--verbose"],
      "timeout_ms": 5000
    }
  }
}
```

## 数据库管理

### 数据库结构

系统使用以下数据表：

1. **monitor_addresses** - 监控地址表
2. **token_transfers** - 转账记录表
3. **incoming_transfers** - 入金记录视图
4. **outgoing_transfers** - 出金记录视图
5. **transfer_summary** - 转账统计视图

### 管理命令

使用Python脚本管理数据库：

```bash
# 添加监控地址
python3 scripts/database_manager.py add 0x1234... ETH "我的钱包"

# 删除监控地址
python3 scripts/database_manager.py remove 0x1234...

# 列出监控地址
python3 scripts/database_manager.py list

# 查询转账记录
python3 scripts/database_manager.py transfers --days 7 --token ETH

# 查询统计信息
python3 scripts/database_manager.py summary --days 30
```

### 直接SQL查询

```sql
-- 查看最近的转账记录
SELECT * FROM token_transfers ORDER BY timestamp DESC LIMIT 10;

-- 查看入金记录
SELECT * FROM incoming_transfers WHERE token_type = 'ETH';

-- 查看出金记录
SELECT * FROM outgoing_transfers WHERE token_type = 'USDT';

-- 查看统计信息
SELECT * FROM transfer_summary;
```

## Go触发器脚本

系统使用Go语言编写的触发器脚本处理转账数据：

- `eth_transfer_handler.go` - 处理ETH转账
- `usdt_transfer_handler.go` - 处理USDT转账
- `usdc_transfer_handler.go` - 处理USDC转账

### 脚本功能

1. **数据解析** - 解析监控匹配的JSON数据
2. **数据库连接** - 连接到MySQL数据库
3. **数据存储** - 将转账信息存储到数据库
4. **错误处理** - 处理各种异常情况
5. **日志记录** - 记录处理过程和结果

### 编译脚本

```bash
cd config/triggers/scripts
go mod tidy
go build -o eth_transfer_handler eth_transfer_handler.go
go build -o usdt_transfer_handler usdt_transfer_handler.go
go build -o usdc_transfer_handler usdc_transfer_handler.go
```

## 监控地址管理

### 添加监控地址

```bash
# 使用Python脚本
python3 scripts/database_manager.py add 0x1234... ETH "我的ETH钱包"

# 或直接SQL
INSERT INTO monitor_addresses (address, token_type, description) 
VALUES ('0x1234...', 'ETH', '我的ETH钱包');
```

### 删除监控地址

```bash
# 使用Python脚本
python3 scripts/database_manager.py remove 0x1234...

# 或直接SQL
UPDATE monitor_addresses SET is_active = FALSE WHERE address = '0x1234...';
```

## 系统管理

### 启动脚本命令

```bash
# 启动监控
./scripts/start_monitor.sh start

# 停止监控
./scripts/start_monitor.sh stop

# 重启监控
./scripts/start_monitor.sh restart

# 查看状态
./scripts/start_monitor.sh status

# 初始化数据库
./scripts/start_monitor.sh init

# 编译脚本
./scripts/start_monitor.sh compile

# 显示帮助
./scripts/start_monitor.sh help
```

### 日志查看

```bash
# 查看监控日志
tail -f logs/monitor.log

# 查看错误日志
grep ERROR logs/monitor.log
```

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查MySQL服务是否运行
   - 验证数据库连接参数
   - 确认数据库用户权限

2. **Go脚本编译失败**
   - 检查Go版本 (需要1.21+)
   - 确认网络连接正常
   - 清理并重新下载依赖

3. **监控服务启动失败**
   - 检查配置文件语法
   - 确认端口未被占用
   - 查看详细错误日志

4. **没有监控到转账**
   - 检查RPC节点连接
   - 确认监控地址正确
   - 验证触发器脚本权限

### 调试模式

启用详细日志：

```bash
# 设置环境变量
export RUST_LOG=debug

# 启动监控
cargo run --release
```

## 性能优化

### 数据库优化

```sql
-- 添加索引
CREATE INDEX idx_timestamp_token ON token_transfers(timestamp, token_type);
CREATE INDEX idx_address_active ON monitor_addresses(address, is_active);

-- 分区表（可选）
ALTER TABLE token_transfers PARTITION BY RANGE (YEAR(timestamp)) (
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026)
);
```

### 监控配置优化

- 调整 `max_past_blocks` 参数
- 优化 `cron_schedule` 频率
- 配置多个RPC节点

## 安全注意事项

1. **数据库安全**
   - 使用强密码
   - 限制数据库访问IP
   - 定期备份数据

2. **RPC节点安全**
   - 使用可信的RPC节点
   - 配置备用节点
   - 监控节点响应时间

3. **脚本安全**
   - 只运行可信的Go脚本
   - 定期更新依赖
   - 监控脚本执行时间

## 扩展功能

### 添加新代币监控

1. 创建新的监控配置文件
2. 编写对应的Go触发器脚本
3. 更新数据库管理脚本
4. 添加新的触发器配置

### 集成其他通知方式

- 邮件通知
- Slack通知
- Discord通知
- Telegram通知
- Webhook通知

## 许可证

本项目基于 GNU Affero General Public License v3.0 许可证。

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 支持

如果您遇到问题，请：

1. 查看本文档的故障排除部分
2. 检查项目日志文件
3. 提交Issue到项目仓库 