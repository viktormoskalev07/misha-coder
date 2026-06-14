#!/bin/bash
# Quick runner to process messages immediately

echo "🚀 Starting Telegram Bot Processing Now..."
echo ""

cd /home/user/misha-coder

# Step 1: Fetch messages from Telegram
echo "📬 Fetching messages from Telegram..."
node .github/workflows/telegram-handler.js

echo ""
echo "⏳ Processing commands..."
# Step 2: Process commands
python3 process-commands.py

echo ""
echo "📤 Sending results..."
# Step 3: Send results
node .github/workflows/send-results.js

echo ""
echo "✅ Done! Committing changes..."
# Step 4: Commit and push
git add -A
git diff --quiet && git diff --staged --quiet || (git commit -m "Bot: Process at $(date)" && git push origin claude/telegram-bot-message-read-6hk5e5)

echo ""
echo "🎉 Processing completed!"
