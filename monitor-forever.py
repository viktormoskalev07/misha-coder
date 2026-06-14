#!/usr/bin/env python3
"""
Eternal Bot Monitor - Never stops, keeps trying to get messages
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
    time_str = datetime.now().strftime('%H:%M:%S')
    print(f"[{time_str}] {msg}")

def execute_command(command):
    """Execute shell command"""
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
        return {"success": False, "output": "Timeout", "code": -1}
    except Exception as e:
        return {"success": False, "output": str(e), "code": -1}

def create_file(filepath, content):
    """Create file"""
    try:
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return {"success": True, "output": f"File: {filepath}", "code": 0}
    except Exception as e:
        return {"success": False, "output": str(e), "code": -1}

def process_task(task_text):
    """Process command"""
    lines = task_text.strip().split('\n')
    command = lines[0].strip()

    if command.startswith("cmd:"):
        return execute_command(command[4:].strip())
    elif command.startswith("file:"):
        parts = command[5:].strip().split('|', 1)
        if len(parts) >= 2:
            return create_file(parts[0].strip(), parts[1].strip())
        return {"success": False, "output": "Invalid format", "code": -1}
    elif command.startswith("git:"):
        return execute_command(f"cd /home/user/misha-coder && git {command[4:].strip()}")
    elif command == "status":
        return execute_command("cd /home/user/misha-coder && git status")
    else:
        return {"success": False, "output": f"Unknown: {command}", "code": -1}

def load_json(filepath):
    """Load JSON"""
    try:
        if filepath.exists():
            return json.loads(filepath.read_text())
    except:
        pass
    return [] if "messages" in str(filepath) else []

def save_json(filepath, data):
    """Save JSON"""
    filepath.write_text(json.dumps(data, indent=2, ensure_ascii=False))

def try_get_messages():
    """Try to get messages via Node.js script"""
    try:
        subprocess.run(
            "node .github/workflows/telegram-handler-v2.js 2>/dev/null",
            shell=True,
            cwd="/home/user/misha-coder",
            timeout=20
        )
    except:
        pass

def process_messages():
    """Process new messages"""
    messages = load_json(MESSAGES_FILE)
    results = load_json(RESULTS_FILE)

    new_count = 0
    for msg in messages:
        msg_id = msg["id"]
        if msg_id in PROCESSED_IDS or msg.get("processed"):
            continue

        PROCESSED_IDS.add(msg_id)
        new_count += 1

        text = msg["text"]
        chat_id = msg["chatId"]
        user_id = msg["userId"]

        log(f"⚙️  Processing from @{user_id}: {text[:40]}")

        result = process_task(text)
        status = "✅" if result["success"] else "❌"
        log(f"{status} {result['output'][:60]}")

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

        msg["processed"] = True
        msg["processedAt"] = datetime.now().isoformat()

    if PROCESSED_IDS:
        save_json(MESSAGES_FILE, messages)
        save_json(RESULTS_FILE, results)

    return new_count

def commit_changes():
    """Commit changes"""
    try:
        subprocess.run("git config user.name 'Bot' 2>/dev/null || true", shell=True, cwd="/home/user/misha-coder")
        subprocess.run("git config user.email 'bot@example.com' 2>/dev/null || true", shell=True, cwd="/home/user/misha-coder")
        subprocess.run("git add -A 2>/dev/null", shell=True, cwd="/home/user/misha-coder")
        result = subprocess.run("git diff --quiet && git diff --staged --quiet", shell=True, cwd="/home/user/misha-coder")

        if result.returncode != 0:
            subprocess.run("git commit -m 'Bot: Messages' 2>/dev/null", shell=True, cwd="/home/user/misha-coder")
            subprocess.run("git push origin claude/telegram-bot-message-read-6hk5e5 2>/dev/null", shell=True, cwd="/home/user/misha-coder")
            log("💾 Committed")
    except:
        pass

def main():
    """Main eternal loop"""
    print("\n" + "="*60)
    print("🤖 ETERNAL BOT MONITOR - NEVER STOPS")
    print("="*60)
    print("⏳ Checking every 10 seconds forever...")
    print("="*60 + "\n")

    cycle = 0
    while True:
        cycle += 1
        log(f"🔄 Cycle {cycle}")

        # Try to get new messages from Telegram
        try_get_messages()

        # Process any new messages
        processed = process_messages()
        if processed > 0:
            log(f"✅ Processed {processed} new message(s)")

        # Commit changes
        commit_changes()

        # Wait
        for i in range(10, 0, -1):
            print(f"  ⏳ {i}s...", end='\r')
            time.sleep(1)
        print("        ")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopped by user")
    except Exception as e:
        log(f"ERROR: {e}")
