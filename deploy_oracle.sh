#!/bin/bash
# Oracle Cloud Deployment Script for Dismissal Checker App

echo "=========================================="
echo "  Dismissal Checker - Oracle Cloud Setup"
echo "=========================================="

# Update system
echo "[1/7] Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python and pip
echo "[2/7] Installing Python and dependencies..."
sudo apt install -y python3 python3-pip python3-venv git nginx

# Create app directory
echo "[3/7] Setting up application directory..."
sudo mkdir -p /var/www/dismissal
sudo chown $USER:$USER /var/www/dismissal
cd /var/www/dismissal

# Clone repository
echo "[4/7] Cloning repository..."
if [ -d ".git" ]; then
    git pull origin main
else
    git clone https://github.com/ibrahimfakhrey/mozoonn.git .
fi

# Create virtual environment
echo "[5/7] Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install requirements
echo "[6/7] Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Create systemd service
echo "[7/7] Setting up systemd service..."
sudo tee /etc/systemd/system/dismissal.service > /dev/null <<EOF
[Unit]
Description=Dismissal Checker Flask App
After=network.target

[Service]
User=$USER
WorkingDirectory=/var/www/dismissal
Environment="PATH=/var/www/dismissal/venv/bin"
ExecStart=/var/www/dismissal/venv/bin/gunicorn --workers 2 --bind 0.0.0.0:8000 flask_app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable dismissal
sudo systemctl start dismissal

# Configure Nginx
sudo tee /etc/nginx/sites-available/dismissal > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/dismissal /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx

# Open firewall ports
echo "Opening firewall ports..."
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save 2>/dev/null || true

echo ""
echo "=========================================="
echo "  Deployment Complete!"
echo "=========================================="
echo ""
echo "Your app should be running at:"
echo "  http://YOUR_SERVER_IP"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status dismissal  - Check app status"
echo "  sudo systemctl restart dismissal - Restart app"
echo "  sudo journalctl -u dismissal -f  - View logs"
echo ""
