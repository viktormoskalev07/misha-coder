#!/bin/bash
# Monitor and process Telegram bot messages

echo "🤖 Bot Message Monitor Started"
echo "📁 Watching: bot-messages.json"
echo "💾 Results: bot-results.json"
echo "⏳ Processing interval: 5 seconds"
echo ""

while true; do
  python3 /home/user/misha-coder/process-commands.py
  sleep 5
done
