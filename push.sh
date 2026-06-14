#!/usr/bin/env bash
# Деплой PR Monitor на сервер одной командой.
# Использование: bash push.sh [user@host] [путь на сервере]
# Примеры:
#   bash push.sh
#   bash push.sh root@83.69.233.40
#   bash push.sh root@83.69.233.40 /opt/pr-monitor

set -euo pipefail

### ── Параметры ─────────────────────────────────────────────────────────────
SSH_TARGET="${1:-root@83.69.233.40}"
REMOTE_DIR="${2:-/opt/pr-monitor}"
SSH_KEY="${SSH_KEY:-}"          # Путь к ключу, если не ~/.ssh/id_rsa
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

### ── Цвета ─────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()    { echo -e "${GREEN}▶ $*${NC}"; }
warn()    { echo -e "${YELLOW}⚠ $*${NC}"; }
error()   { echo -e "${RED}✗ $*${NC}"; exit 1; }

### ── SSH-опции ─────────────────────────────────────────────────────────────
SSH_OPTS="-o StrictHostKeyChecking=accept-new -o ConnectTimeout=10"
if [[ -n "$SSH_KEY" ]]; then
    SSH_OPTS="$SSH_OPTS -i $SSH_KEY"
fi
SSH="ssh $SSH_OPTS"
RSYNC_SSH="ssh $SSH_OPTS"

### ── Проверка доступности ──────────────────────────────────────────────────
info "Проверяю подключение к $SSH_TARGET..."
if ! $SSH "$SSH_TARGET" "echo ok" &>/dev/null; then
    echo ""
    warn "Не удалось подключиться без пароля."
    echo ""
    echo "Для беспарольного входа выполни один раз:"
    echo ""
    echo "  ssh-keygen -t ed25519 -f ~/.ssh/id_pr_monitor -N ''"
    echo "  ssh-copy-id -i ~/.ssh/id_pr_monitor.pub $SSH_TARGET"
    echo ""
    echo "Или запусти с явным ключом:"
    echo "  SSH_KEY=~/.ssh/id_pr_monitor bash push.sh"
    echo ""
    error "Нет SSH-доступа. Настрой ключ и попробуй снова."
fi

### ── Синхронизация кода ────────────────────────────────────────────────────
info "Синхронизирую код → $SSH_TARGET:$REMOTE_DIR ..."
rsync -az --delete \
    -e "$RSYNC_SSH" \
    --exclude='data/' \
    --exclude='outputs/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='mockup.html' \
    --exclude='remote_page.html' \
    --exclude='node_modules/' \
    --exclude='.git/' \
    "$SCRIPT_DIR/" \
    "$SSH_TARGET:$REMOTE_DIR/"

### ── pip install на сервере (если нужен anthropic) ────────────────────────
info "Устанавливаю зависимости на сервере (если изменились)..."
$SSH "$SSH_TARGET" "cd $REMOTE_DIR && docker compose exec -T app pip install -q anthropic>=0.105.0 2>/dev/null || true"

### ── Пересборка и перезапуск контейнера ────────────────────────────────────
info "Пересобираю и перезапускаю контейнер..."
$SSH "$SSH_TARGET" "cd $REMOTE_DIR && docker compose up -d --build"

### ── Проверка ──────────────────────────────────────────────────────────────
info "Жду запуска (5 сек)..."
sleep 5
HTTP_CODE=$($SSH "$SSH_TARGET" "curl -s -o /dev/null -w '%{http_code}' --connect-timeout 5 http://localhost:8765/ || echo 000")
if [[ "$HTTP_CODE" == "303" || "$HTTP_CODE" == "200" ]]; then
    echo ""
    echo -e "${GREEN}✓ Готово! Сайт работает: http://83.69.233.40/${NC}"
else
    warn "Контейнер запущен, но HTTP ответил $HTTP_CODE. Проверь логи:"
    echo "  $SSH $SSH_TARGET 'docker compose logs --tail=30 app'"
fi
