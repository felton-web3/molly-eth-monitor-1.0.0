#!/bin/bash

# ETH链监控系统快速安装脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查系统要求
check_system_requirements() {
    print_step "检查系统要求..."
    
    # 检查操作系统
    if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]]; then
        print_info "✓ 操作系统支持"
    else
        print_error "✗ 不支持的操作系统: $OSTYPE"
        exit 1
    fi
    
    # 检查Rust
    if command -v rustc &> /dev/null; then
        local rust_version=$(rustc --version | cut -d' ' -f2)
        print_info "✓ Rust已安装: $rust_version"
    else
        print_error "✗ Rust未安装，请先安装Rust: https://rustup.rs/"
        exit 1
    fi
    
    # 检查Go
    if command -v go &> /dev/null; then
        local go_version=$(go version | cut -d' ' -f3)
        print_info "✓ Go已安装: $go_version"
    else
        print_error "✗ Go未安装，请先安装Go: https://golang.org/dl/"
        exit 1
    fi
    
    # 检查MySQL
    if command -v mysql &> /dev/null; then
        print_info "✓ MySQL客户端已安装"
    else
        print_warning "⚠ MySQL客户端未安装，请安装MySQL客户端"
    fi
    
    # 检查Python3
    if command -v python3 &> /dev/null; then
        print_info "✓ Python3已安装"
    else
        print_warning "⚠ Python3未安装，数据库管理功能可能不可用"
    fi
    
    # 检查jq
    if command -v jq &> /dev/null; then
        print_info "✓ jq已安装"
    else
        print_warning "⚠ jq未安装，请安装jq用于JSON处理"
    fi
}

# 安装Python依赖
install_python_deps() {
    print_step "安装Python依赖..."
    
    if command -v python3 &> /dev/null; then
        if python3 -c "import mysql.connector" > /dev/null 2>&1; then
            print_info "✓ mysql-connector-python已安装"
        else
            print_info "安装mysql-connector-python..."
            if pip3 install mysql-connector-python; then
                print_info "✓ mysql-connector-python安装成功"
            else
                print_warning "⚠ mysql-connector-python安装失败，请手动安装"
            fi
        fi
    else
        print_warning "⚠ Python3未安装，跳过Python依赖安装"
    fi
}

# 配置环境变量
setup_environment() {
    print_step "配置环境变量..."
    
    if [ ! -f ".env" ]; then
        print_info "创建.env文件..."
        cp env.example .env
        print_info "✓ .env文件已创建，请编辑数据库配置"
    else
        print_info "✓ .env文件已存在"
    fi
}

# 编译Go脚本
compile_go_scripts() {
    print_step "编译Go脚本..."
    
    cd config/triggers/scripts
    
    # 初始化Go模块
    if [ ! -f "go.mod" ]; then
        go mod init blockchain-monitor-scripts
    fi
    
    # 下载依赖
    print_info "下载Go依赖..."
    if go mod tidy; then
        print_info "✓ Go依赖下载成功"
    else
        print_warning "⚠ Go依赖下载失败，可能需要网络连接"
    fi
    
    # 编译脚本
    print_info "编译Go脚本..."
    for script in eth_transfer_handler.go usdt_transfer_handler.go usdc_transfer_handler.go; do
        if go build -o "${script%.go}" "$script"; then
            print_info "✓ $script 编译成功"
        else
            print_error "✗ $script 编译失败"
            cd ../../..
            return 1
        fi
    done
    
    cd ../../..
    print_info "✓ 所有Go脚本编译完成"
}

# 初始化数据库
init_database() {
    print_step "初始化数据库..."
    
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
    
    # 创建数据库和表
    if command -v mysql &> /dev/null; then
        print_info "创建数据库和表..."
        if mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" < scripts/database_setup.sql; then
            print_info "✓ 数据库初始化成功"
        else
            print_warning "⚠ 数据库初始化失败，请检查数据库连接"
        fi
    else
        print_warning "⚠ MySQL客户端未安装，请手动执行 scripts/database_setup.sql"
    fi
}

# 测试配置
test_configuration() {
    print_step "测试配置..."
    
    if ./scripts/test_config.sh; then
        print_info "✓ 配置测试通过"
    else
        print_warning "⚠ 配置测试失败，请检查错误信息"
    fi
}

# 显示完成信息
show_completion_info() {
    echo ""
    print_info "🎉 安装完成！"
    echo ""
    print_info "下一步操作："
    echo "1. 编辑 .env 文件，配置数据库连接信息"
    echo "2. 运行 './scripts/start_monitor.sh start' 启动监控"
    echo "3. 运行 './scripts/start_monitor.sh status' 查看状态"
    echo ""
    print_info "管理命令："
    echo "• 启动监控: ./scripts/start_monitor.sh start"
    echo "• 停止监控: ./scripts/start_monitor.sh stop"
    echo "• 查看状态: ./scripts/start_monitor.sh status"
    echo "• 重启监控: ./scripts/start_monitor.sh restart"
    echo ""
    print_info "数据库管理："
    echo "• 添加监控地址: python3 scripts/database_manager.py add <地址> <代币类型>"
    echo "• 删除监控地址: python3 scripts/database_manager.py remove <地址>"
    echo "• 查看转账记录: python3 scripts/database_manager.py transfers"
    echo "• 查看统计信息: python3 scripts/database_manager.py summary"
    echo ""
    print_info "文档："
    echo "• 详细文档: ETH_MONITOR_README.md"
    echo "• 配置文件: config/ 目录"
    echo "• 脚本文件: scripts/ 目录"
}

# 主函数
main() {
    echo ""
    print_info "🚀 ETH链监控系统快速安装"
    echo ""
    
    # 检查系统要求
    check_system_requirements
    
    # 安装Python依赖
    install_python_deps
    
    # 配置环境变量
    setup_environment
    
    # 编译Go脚本
    compile_go_scripts
    
    # 初始化数据库
    init_database
    
    # 测试配置
    test_configuration
    
    # 显示完成信息
    show_completion_info
}

# 运行主函数
main "$@" 