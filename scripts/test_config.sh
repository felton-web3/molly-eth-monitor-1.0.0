#!/bin/bash

# 配置测试脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 测试配置文件
test_config_files() {
    print_info "测试配置文件..."
    
    # 检查网络配置
    if [ -f "config/networks/ethereum_mainnet.json" ]; then
        if jq . config/networks/ethereum_mainnet.json > /dev/null 2>&1; then
            print_info "✓ ETH主网配置有效"
        else
            print_error "✗ ETH主网配置无效"
            return 1
        fi
    else
        print_error "✗ 缺少ETH主网配置文件"
        return 1
    fi
    
    # 检查监控配置
    for monitor in eth_transfer_monitor usdt_transfer_monitor usdc_transfer_monitor; do
        if [ -f "config/monitors/${monitor}.json" ]; then
            if jq . config/monitors/${monitor}.json > /dev/null 2>&1; then
                print_info "✓ ${monitor}配置有效"
            else
                print_error "✗ ${monitor}配置无效"
                return 1
            fi
        else
            print_error "✗ 缺少${monitor}配置文件"
            return 1
        fi
    done
    
    # 检查触发器配置
    if [ -f "config/triggers/database_notifications.json" ]; then
        if jq . config/triggers/database_notifications.json > /dev/null 2>&1; then
            print_info "✓ 数据库触发器配置有效"
        else
            print_error "✗ 数据库触发器配置无效"
            return 1
        fi
    else
        print_error "✗ 缺少数据库触发器配置文件"
        return 1
    fi
    
    print_info "所有配置文件测试通过"
}

# 测试Python脚本
test_python_scripts() {
    print_info "测试Python脚本..."
    
    cd config/triggers/scripts
    
    # 检查Python脚本文件
    for script in eth_transfer_handler.py usdt_transfer_handler.py usdc_transfer_handler.py; do
        if [ -f "$script" ]; then
            print_info "✓ $script 存在"
        else
            print_error "✗ 缺少 $script"
            cd ../../..
            return 1
        fi
    done
    
    # 检查Python依赖
    if command -v python3 &> /dev/null; then
        if python3 -c "import mysql.connector" > /dev/null 2>&1; then
            print_info "✓ Python依赖检查通过"
        else
            print_warning "⚠ 缺少mysql-connector-python，请安装: pip3 install mysql-connector-python"
        fi
    else
        print_error "✗ Python3未安装"
        cd ../../..
        return 1
    fi
    
    cd ../../..
    print_info "Python脚本测试完成"
}

# 测试数据库连接
test_database_connection() {
    print_info "测试数据库连接..."
    
    # 加载环境变量
    if [ -f ".env" ]; then
        export $(cat .env | grep -v '^#' | xargs)
    fi
    
    # 设置默认值
    DB_HOST=${DB_HOST:-localhost}
    DB_PORT=${DB_PORT:-3306}
    DB_USER=${DB_USER:-root}
    DB_PASSWORD=${DB_PASSWORD:-}
    DB_NAME=${DB_NAME:-blockchain_monitor}
    
    # 测试连接
    if command -v mysql &> /dev/null; then
        if mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" -e "SELECT 1" > /dev/null 2>&1; then
            print_info "✓ 数据库连接成功"
            
            # 检查数据库是否存在
            if mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" -e "USE $DB_NAME" > /dev/null 2>&1; then
                print_info "✓ 数据库 $DB_NAME 存在"
            else
                print_warning "⚠ 数据库 $DB_NAME 不存在，需要初始化"
            fi
        else
            print_error "✗ 数据库连接失败"
            return 1
        fi
    else
        print_warning "⚠ MySQL客户端未安装，跳过数据库测试"
    fi
}

# 测试Python脚本
test_python_scripts() {
    print_info "测试Python脚本..."
    
    if command -v python3 &> /dev/null; then
        if [ -f "scripts/database_manager.py" ]; then
            if python3 -c "import mysql.connector" > /dev/null 2>&1; then
                print_info "✓ Python依赖检查通过"
            else
                print_warning "⚠ 缺少mysql-connector-python，请安装: pip3 install mysql-connector-python"
            fi
        else
            print_error "✗ 缺少数据库管理脚本"
            return 1
        fi
    else
        print_warning "⚠ Python3未安装，跳过Python脚本测试"
    fi
}

# 主函数
main() {
    print_info "开始配置测试..."
    
    local all_passed=true
    
    # 测试配置文件
    if ! test_config_files; then
        all_passed=false
    fi
    
    # 测试Python脚本
    if ! test_python_scripts; then
        all_passed=false
    fi
    
    # 测试数据库连接
    if ! test_database_connection; then
        all_passed=false
    fi
    
    # 测试Python脚本
    if ! test_python_scripts; then
        all_passed=false
    fi
    
    echo ""
    if [ "$all_passed" = true ]; then
        print_info "所有测试通过！系统配置正确。"
        print_info "您可以运行 './scripts/start_monitor.sh start' 来启动监控。"
    else
        print_error "部分测试失败，请检查上述错误信息。"
        exit 1
    fi
}

# 运行主函数
main "$@" 