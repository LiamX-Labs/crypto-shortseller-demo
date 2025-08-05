#!/bin/bash
# Server Update Script for Multi-Asset Trading System
# Usage: ./update_server.sh

echo "🔄 Updating server with latest changes..."

# Define server connection
SERVER="Liam@104.43.88.185"
KEY="~/AWS/Lxalgo_key.pem"
SERVER_PATH="/home/Liam/tradingbots/shortseller"

# Create backup on server
echo "📦 Creating backup on server..."
ssh -i $KEY $SERVER "cd /home/Liam/tradingbots && cp -r shortseller shortseller_backup_\$(date +%Y%m%d_%H%M%S)"

# Sync code changes (excluding venv and logs)
echo "📡 Syncing code changes..."
rsync -avz --exclude='venv' --exclude='logs' --exclude='.git/objects' \
    -e "ssh -i $KEY" \
    . $SERVER:$SERVER_PATH/

# Update git repository structure
echo "🔄 Updating git repository..."
rsync -avz -e "ssh -i $KEY" .git/ $SERVER:$SERVER_PATH/.git/

# Verify update
echo "✅ Verifying server update..."
ssh -i $KEY $SERVER "cd $SERVER_PATH && git log --oneline -1"

echo "🚀 Server update completed successfully!"
echo "📋 To start the system: ssh -i $KEY $SERVER 'cd $SERVER_PATH && source venv/bin/activate && python3 scripts/start_trading.py'"