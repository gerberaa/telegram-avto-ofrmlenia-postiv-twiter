#!/bin/bash

# 1. Оновлення системи та встановлення Python і pip
sudo apt update
sudo apt install -y python3 python3-pip git

# 2. Клонування репозиторію (заміни на свій, якщо потрібно)
# git clone https://github.com/gerberaa/telegram-avto-ofrmlenia-postiv-twiter.git
# cd telegram-avto-ofrmlenia-postiv-twiter

# Якщо файли вже є локально:
cd ~/telegram-avto-ofrmlenia-postiv-twiter || cd ~

# 3. Створення requirements.txt (якщо ще немає)
cat > requirements.txt <<EOF
aiogram
requests
EOF

# 4. Встановлення залежностей
pip3 install -r requirements.txt

# 5. Створення systemd-сервісу
SERVICE_FILE=/etc/systemd/system/telegram-bot.service
sudo bash -c "cat > \$SERVICE_FILE" <<EOL
[Unit]
Description=Telegram AI Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=$(pwd)
ExecStart=$(which python3) bot.py
Restart=always
User=$USER

[Install]
WantedBy=multi-user.target
EOL

# 6. Дозвіл на запуск та автозапуск
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot
sudo systemctl restart telegram-bot

echo "✅ Бот встановлено та запущено як systemd-сервіс!"
echo "Перевірити статус: sudo systemctl status telegram-bot"
