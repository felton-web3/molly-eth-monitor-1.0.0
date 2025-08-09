#!/bin/bash

# ETH链监控启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    print_info "检查依赖..."
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python3未安装，请先安装Python3"
        exit 1
    fi
    
    # 检查MySQL
    if ! command -v mysql &> /dev/null; then
        print_warning "MySQL客户端未安装，但可以继续运行"
    fi
    
    print_info "依赖检查完成"
}

# 设置环境变量
setup_environment() {
    print_info "设置环境变量..."
    
    # 加载.env文件
    if [ -f ".env" ]; then
        export $(cat .env | grep -v '^#' | xargs)
        print_info "已加载.env文件"
    else
        print_warning "未找到.env文件，使用默认配置"
    fi
    
    # 设置默认值
    export DB_HOST=${DB_HOST:-localhost}
    export DB_PORT=${DB_PORT:-3306}
    export DB_USER=${DB_USER:-root}
    export DB_PASSWORD=${DB_PASSWORD:-}
    export DB_NAME=${DB_NAME:-blockchain_monitor}
}

# 初始化数据库
init_database() {
    print_info "初始化数据库..."
    
    if [ -z "$DB_PASSWORD" ]; then
        print_warning "数据库密码未设置，请确保数据库已正确配置"
    fi
    
    # 创建数据库和表
    if command -v mysql &> /dev/null; then
        mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" < scripts/database_setup.sql
        print_info "数据库初始化完成"
    else
        print_warning "MySQL客户端未安装，请手动执行 scripts/database_setup.sql"
    fi
}

# 检查Python脚本
check_scripts() {
    print_info "检查Python脚本..."
    
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
    print_info "✓ Python脚本检查完成"
}

# 启动监控
start_monitor() {
    print_info "启动区块链监控..."
    
    # 创建日志目录
    mkdir -p logs
    
    # 启动监控服务
    cargo run --release 2>&1 | tee logs/monitor.log &
    
    MONITOR_PID=$!
    echo $MONITOR_PID > .monitor.pid
    
    print_info "监控服务已启动，PID: $MONITOR_PID"
    print_info "日志文件: logs/monitor.log"
}

# 显示状态
show_status() {
    print_info "监控状态:"
    
    if [ -f ".monitor.pid" ]; then
        PID=$(cat .monitor.pid)
        if ps -p $PID > /dev/null 2>&1; then
            print_info "监控服务正在运行 (PID: $PID)"
        else
            print_warning "监控服务未运行"
        fi
    else
        print_warning "未找到PID文件"
    fi
    
    # 显示数据库连接状态
    if command -v mysql &> /dev/null; then
        if mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" -e "SELECT 1" > /dev/null 2>&1; then
            print_info "数据库连接正常"
        else
            print_error "数据库连接失败"
        fi
    fi
}

# 停止监控
stop_monitor() {
    print_info "停止监控服务..."
    
    if [ -f ".monitor.pid" ]; then
        PID=$(cat .monitor.pid)
        if ps -p $PID > /dev/null 2>&1; then
            kill $PID
            print_info "已停止监控服务 (PID: $PID)"
        else
            print_warning "监控服务未运行"
        fi
        rm -f .monitor.pid
    else
        print_warning "未找到PID文件"
    fi
}

# 显示帮助
show_help() {
    echo "ETH链监控系统"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  start     启动监控服务"
    echo "  stop      停止监控服务"
    echo "  restart   重启监控服务"
    echo "  status    显示服务状态"
    echo "  init      初始化数据库"
    echo "  compile   检查Python脚本"
    echo "  help      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 start    # 启动监控"
    echo "  $0 status   # 查看状态"
    echo "  $0 stop     # 停止监控"
}

# 主函数
main() {
    case "${1:-start}" in
        start)
            check_dependencies
            setup_environment
            check_scripts
            init_database
            start_monitor
            show_status
            ;;
        stop)
            stop_monitor
            ;;
        restart)
            stop_monitor
            sleep 2
            check_dependencies
            setup_environment
            check_scripts
            start_monitor
            show_status
            ;;
        status)
            setup_environment
            show_status
            ;;
        init)
            setup_environment
            init_database
            ;;
        compile)
            check_scripts
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@" 