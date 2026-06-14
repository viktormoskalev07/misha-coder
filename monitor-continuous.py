#!/usr/bin/env python3
"""
Continuous Telegram Bot Monitor
Watches for new messages and processes them immediately
"""

import json
import subprocess
import time
import os
from pathlib import Path
from datetime import datetime

MESSAGES_FILE = Path("bot-messages.json")
RESULTS_FILE = Path("bot-results.json")
PROCESSED_IDS = set()

def log(msg):
    """Log with timestamp"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def execute_command(command):
    """Execute shell command safely"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd="/home/user/misha-coder"
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout or result.stderr,
            "code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "Command timeout (>30s)",
            "code": -1
        }
    except Exception as e:
        return {
            "success": False,
            "output": str(e),
            "code": -1
        }

def create_file(filepath, content):
    """Create or update a file"""
    try:
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return {
            "success": True,
            "output": f"File created: {filepath}",
            "code": 0
        }
    except Exception as e:
        return {
            "success": False,
            "output": str(e),
            "code": -1
        }

def process_task(task_text):
    """Process incoming task"""
    lines = task_text.strip().split('\n')
    command = lines[0].strip()

    if command.startswith("cmd:"):
        cmd = command[4:].strip()
        return execute_command(cmd)

    elif command.startswith("file:"):
        parts = command[5:].strip().split('|', 1)
        if len(parts) >= 2:
            filepath = parts[0].strip()
            content = parts[1].strip()
            return create_file(filepath, content)
        return {"success": False, "output": "Invalid file format: use 'file: path | content'", "code": -1}

    elif command.startswith("git:"):
        cmd = command[4:].strip()
        return execute_command(f"cd /home/user/misha-coder && git {cmd}")

    elif command == "status":
        result = execute_command("cd /home/user/misha-coder && git status")
        return result

    else:
        return {"success": False, "output": f"Unknown command: {command}", "code": -1}

def load_json(filepath):
    """Load JSON file"""
    try:
        if filepath.exists():
            return json.loads(filepath.read_text())
        return []
    except:
        return []

def save_json(filepath, data):
    """Save JSON file"""
    filepath.write_text(json.dumps(data, indent=2, ensure_ascii=False))

def process_messages():
    """Check for new messages and process them"""
    messages = load_json(MESSAGES_FILE)
    results = load_json(RESULTS_FILE)

    for msg in messages:
        msg_id = msg["id"]

        # Skip if already processed
        if msg_id in PROCESSED_IDS or msg.get("processed"):
            continue

        PROCESSED_IDS.add(msg_id)
        text = msg["text"]
        chat_id = msg["chatId"]
        user_id = msg["userId"]

        log(f"📬 New message from @{user_id}: {text}")

        # Execute task
        result = process_task(text)

        # Format result
        status = "✅" if result["success"] else "❌"
        output_preview = result["output"][:100].replace('\n', ' ')
        log(f"{status} Executed: {output_preview}...")

        # Add result
        results.append({
            "id": msg_id,
            "timestamp": datetime.now().isoformat(),
            "userId": user_id,
            "chatId": chat_id,
            "command": text,
            "success": result["success"],
            "output": result["output"],
            "code": result["code"],
            "sent": False
        })

        # Mark as processed
        msg["processed"] = True
        msg["processedAt"] = datetime.now().isoformat()

    if PROCESSED_IDS:
        save_json(MESSAGES_FILE, messages)
        save_json(RESULTS_FILE, results)

def commit_changes():
    """Commit and push changes"""
    try:
        subprocess.run("git config user.name 'Bot' 2>/dev/null || true", shell=True, cwd="/home/user/misha-coder")
        subprocess.run("git config user.email 'bot@example.com' 2>/dev/null || true", shell=True, cwd="/home/user/misha-coder")
        subprocess.run("git add -A 2>/dev/null", shell=True, cwd="/home/user/misha-coder")
        result = subprocess.run("git diff --quiet && git diff --staged --quiet", shell=True, cwd="/home/user/misha-coder")

        if result.returncode != 0:
            subprocess.run("git commit -m 'Bot: Process messages' 2>/dev/null", shell=True, cwd="/home/user/misha-coder")
            subprocess.run("git push origin claude/telegram-bot-message-read-6hk5e5 2>/dev/null", shell=True, cwd="/home/user/misha-coder")
            log("💾 Changes committed and pushed")
    except:
        pass

def main():
    """Main loop"""
    print("\n" + "="*60)
    print("🤖 TELEGRAM BOT MONITOR - CONTINUOUS MODE")
    print("="*60)
    print("📍 Watching: bot-messages.json")
    print("📤 Results: bot-results.json")
    print("⏳ Checking every 5 seconds...")
    print("="*60 + "\n")

    try:
        while True:
            process_messages()
            commit_changes()
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n\n⏹️  Monitor stopped by user")
    except Exception as e:
        log(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
