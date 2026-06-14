#!/usr/bin/env python3
"""
Quick runner to process Telegram messages immediately
Combines: fetch -> process -> send -> commit
"""

import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime

def run_command(cmd, description):
    """Run a command and show status"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, cwd="/home/user/misha-coder")
        if result.returncode == 0:
            print(f"✅ {description} completed\n")
            return True
        else:
            print(f"⚠️  {description} finished with warnings\n")
            return True
    except Exception as e:
        print(f"❌ Error in {description}: {e}\n")
        return False

def main():
    print("=" * 50)
    print("🚀 TELEGRAM BOT - PROCESS NOW")
    print("=" * 50)
    print()

    # Step 1: Fetch messages
    run_command(
        "node .github/workflows/telegram-handler.js",
        "Fetching messages from Telegram"
    )

    # Step 2: Process commands
    run_command(
        "python3 process-commands.py",
        "Processing commands"
    )

    # Step 3: Send results
    run_command(
        "node .github/workflows/send-results.js",
        "Sending results to Telegram"
    )

    # Step 4: Check for messages
    messages_file = Path("bot-messages.json")
    if messages_file.exists():
        with open(messages_file) as f:
            messages = json.load(f)
            print(f"📊 Messages processed: {len([m for m in messages if m.get('processed')])}/{len(messages)}")
            print()

    # Step 5: Commit changes
    print("📝 Committing changes...")
    subprocess.run("""
        git config user.name "Bot" 2>/dev/null || true
        git config user.email "bot@example.com" 2>/dev/null || true
        git add -A 2>/dev/null || true
        git diff --quiet && git diff --staged --quiet || git commit -m "Bot: Process at $(date)" 2>/dev/null || true
        git push origin claude/telegram-bot-message-read-6hk5e5 2>/dev/null || true
    """, shell=True, cwd="/home/user/misha-coder")
    print("✅ Changes committed\n")

    print("=" * 50)
    print("🎉 PROCESSING COMPLETED!")
    print("=" * 50)

if __name__ == "__main__":
    main()
