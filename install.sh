#!/bin/bash
set -e

APP_DIR="/opt/unified_bot"
LOG_DIR="/var/log/unified_bot"
SERVICE_FILE="/etc/systemd/system/unified-bot.service"

echo "==> Paketler kuruluyor..."
apt-get update -y
apt-get install -y python3 python3-venv python3-pip curl

echo "==> botuser oluşturuluyor..."
id -u botuser &>/dev/null || useradd -r -m -s /bin/bash botuser

echo "==> Dizinler..."
mkdir -p "$APP_DIR" "$LOG_DIR"
chown -R botuser:botuser "$APP_DIR" "$LOG_DIR"

echo "==> Sanal ortam..."
sudo -u botuser python3 -m venv "$APP_DIR/venv"
sudo -u botuser "$APP_DIR/venv/bin/pip" install --upgrade pip
sudo -u botuser "$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"

echo "==> Systemd servisi..."
cp "$APP_DIR/unified-bot.service" "$SERVICE_FILE"
chmod 644 "$SERVICE_FILE"
systemctl daemon-reload
systemctl enable unified-bot
systemctl restart unified-bot

echo "==> Durum:"
sleep 3
systemctl status unified-bot --no-pager
echo ""
echo "✅ Kurulum tamam. Log: journalctl -u unified-bot -f"