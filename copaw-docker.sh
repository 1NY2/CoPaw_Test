#!/bin/bash
# CoPaw Docker 一键启动脚本
# 用法: ./copaw-docker.sh [start|stop|restart|logs|status]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTAINER_NAME="copaw"
IMAGE_NAME="copaw:latest"
PORT="${COPAW_PORT:-8088}"

# 主机上的 CoPaw 配置目录（默认 ~/.copaw）
HOST_COPAW_DIR="${COPAW_HOST_DIR:-$HOME/.copaw}"

# providers.json 路径（模型配置）
PROVIDERS_JSON_SRC="${SCRIPT_DIR}/src/copaw/providers/providers.json"

show_help() {
    echo "CoPaw Docker 管理脚本"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  start    启动 CoPaw 容器"
    echo "  stop     停止 CoPaw 容器"
    echo "  restart  重启 CoPaw 容器"
    echo "  logs     查看容器日志"
    echo "  status   查看容器状态"
    echo "  shell    进入容器 shell"
    echo "  clean      清理容器（保留配置）"
    echo "  clean-all  清理容器和配置（危险）"
    echo ""
    echo "环境变量:"
    echo "  COPAW_PORT       设置端口 (默认: 8088)"
    echo "  COPAW_API_KEY    设置 API Key"
    echo "  COPAW_HOST_DIR   主机配置目录 (默认: ~/.copaw)"
    echo ""
}

start() {
    echo "🚀 启动 CoPaw 容器..."
    echo "📁 使用主机配置目录: ${HOST_COPAW_DIR}"
    
    # 确保主机配置目录存在
    mkdir -p "${HOST_COPAW_DIR}"
    
    # 检查 providers.json 是否存在
    if [[ ! -f "${PROVIDERS_JSON_SRC}" ]]; then
        echo "⚠️  未找到 providers.json: ${PROVIDERS_JSON_SRC}"
        echo "   将使用容器内的默认模型配置"
    else
        echo "📋 使用模型配置: ${PROVIDERS_JSON_SRC}"
    fi
    
    # 检查容器是否已存在
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo "检测到已存在的容器，正在移除..."
        docker rm -f "${CONTAINER_NAME}" > /dev/null 2>&1
    fi
    
    # 构建挂载参数
    MOUNT_ARGS=(
        -v "${HOST_COPAW_DIR}:/app/.copaw"
    )
    
    # 挂载 providers.json（如果存在）
    if [[ -f "${PROVIDERS_JSON_SRC}" ]]; then
        MOUNT_ARGS+=(
            -v "${PROVIDERS_JSON_SRC}:/app/venv/lib/python3.11/site-packages/copaw/providers/providers.json"
        )
    fi
    
    # 启动容器
    docker run -d \
        --name "${CONTAINER_NAME}" \
        -p "${PORT}:8088" \
        "${MOUNT_ARGS[@]}" \
        -e COPAW_WORKING_DIR=/app/.copaw \
        -e COPAW_PORT=8088 \
        -e COPAW_API_KEY="${COPAW_API_KEY:-}" \
        --add-host=host.docker.internal:host-gateway \
        --restart unless-stopped \
        "${IMAGE_NAME}"
    
    echo "✅ CoPaw 已启动！"
    echo ""
    echo "访问地址:"
    echo "  - Web 控制台: http://localhost:${PORT}"
    echo ""
    echo "配置目录: ${HOST_COPAW_DIR}"
    echo ""
    if [[ -f "${PROVIDERS_JSON_SRC}" ]]; then
        echo "⚠️  注意: 如果使用 Ollama 本地模型，需要将配置中的"
        echo "   'localhost:11434' 改为 'host.docker.internal:11434'"
        echo ""
    fi
    echo "查看日志: $0 logs"
}

stop() {
    echo "🛑 停止 CoPaw 容器..."
    docker stop "${CONTAINER_NAME}" > /dev/null 2>&1 || true
    docker rm "${CONTAINER_NAME}" > /dev/null 2>&1 || true
    echo "✅ CoPaw 已停止"
}

restart() {
    stop
    start
}

logs() {
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        docker logs -f "${CONTAINER_NAME}"
    else
        echo "❌ 容器未运行"
        exit 1
    fi
}

status() {
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo "✅ CoPaw 正在运行"
        echo ""
        docker ps --filter "name=${CONTAINER_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        echo ""
        echo "访问地址: http://localhost:${PORT}"
    elif docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo "⏹️  CoPaw 容器已停止"
        docker ps -a --filter "name=${CONTAINER_NAME}" --format "table {{.Names}}\t{{.Status}}"
    else
        echo "❌ CoPaw 容器不存在"
    fi
}

shell() {
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        docker exec -it "${CONTAINER_NAME}" /bin/bash
    else
        echo "❌ 容器未运行"
        exit 1
    fi
}

clean() {
    echo "⚠️  这将删除 CoPaw 容器！"
    echo "📁 配置目录不会删除: ${HOST_COPAW_DIR}"
    read -p "确定要继续吗? (y/N): " confirm
    if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
        stop
        echo "✅ 容器已删除，配置保留在: ${HOST_COPAW_DIR}"
    else
        echo "已取消"
    fi
}

clean_all() {
    echo "⚠️  警告：这将删除 CoPaw 容器和所有配置数据！"
    echo "🗑️  将要删除的目录: ${HOST_COPAW_DIR}"
    read -p "确定要继续吗? 输入 'yes' 确认: " confirm
    if [[ $confirm == "yes" ]]; then
        stop
        echo "🗑️  删除配置目录: ${HOST_COPAW_DIR}"
        rm -rf "${HOST_COPAW_DIR}"
        echo "✅ 清理完成"
    else
        echo "已取消"
    fi
}

# 主逻辑
case "${1:-}" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    logs)
        logs
        ;;
    status)
        status
        ;;
    shell)
        shell
        ;;
    clean)
        clean
        ;;
    clean-all)
        clean_all
        ;;
    *)
        show_help
        ;;
esac
