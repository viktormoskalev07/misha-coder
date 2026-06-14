#!/usr/bin/env python3
"""
Local command processor for Telegram Bot
Reads from bot-messages.json, executes commands, writes to bot-results.json
"""

import json
import subprocess
import os
from pathlib import Path
from datetime import datetime

MESSAGES_FILE = Path("bot-messages.json")
RESULTS_FILE = Path("bot-results.json")

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

    # Parse command
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

def main():
    print(f"[{datetime.now().isoformat()}] Processing commands...")

    # Load messages
    messages = load_json(MESSAGES_FILE)
    results = load_json(RESULTS_FILE)

    if not messages:
        print("No messages to process")
        return

    # Process unprocessed messages
    for msg in messages:
        if msg.get("processed"):
            continue

        msg_id = msg["id"]
        text = msg["text"]
        chat_id = msg["chatId"]
        user_id = msg["userId"]

        print(f"Processing message {msg_id} from @{user_id}")

        # Execute task
        result = process_task(text)

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

    # Save updated data
    save_json(MESSAGES_FILE, messages)
    save_json(RESULTS_FILE, results)

    print(f"✅ Processed {len([m for m in messages if m.get('processed')])} messages")

if __name__ == "__main__":
    main()
