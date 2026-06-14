#!/usr/bin/env python3
"""
Telegram Bot Handler for misha-coder project
Listens for commands and executes tasks
"""

import requests
import json
import subprocess
import os
from datetime import datetime

# Bot token - KEEP SECURE
BOT_TOKEN = "8598513999:AAFhhzutC-6CNon6olbozTsPQgedNYneKp0"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Store update offset for polling
last_update_id = 0

def send_message(chat_id, text):
    """Send a message to Telegram chat"""
    url = f"{TELEGRAM_API}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=data)
        return response.json()
    except Exception as e:
        print(f"Error sending message: {e}")
        return None

def execute_command(command):
    """Execute shell command safely"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
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
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
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
        parts = command[5:].strip().split('|')
        if len(parts) >= 2:
            filepath = parts[0].strip()
            content = '|'.join(parts[1:]).strip()
            return create_file(filepath, content)
        return {"success": False, "output": "Invalid file format", "code": -1}

    elif command.startswith("git:"):
        cmd = command[4:].strip()
        return execute_command(f"cd /home/user/misha-coder && git {cmd}")

    elif command == "status":
        result = execute_command("cd /home/user/misha-coder && git status")
        return result

    else:
        return {"success": False, "output": f"Unknown command: {command}", "code": -1}

def get_updates():
    """Get updates from Telegram"""
    global last_update_id
    url = f"{TELEGRAM_API}/getUpdates"
    params = {"offset": last_update_id + 1, "timeout": 30}

    try:
        response = requests.get(url, params=params, timeout=35)
        data = response.json()

        if data.get("ok"):
            return data.get("result", [])
        return []
    except Exception as e:
        print(f"Error getting updates: {e}")
        return []

def handle_message(message):
    """Handle incoming message"""
    chat_id = message["chat"]["id"]
    text = message.get("text", "")
    user = message["from"].get("username", "unknown")

    print(f"[{datetime.now()}] Message from @{user}: {text[:50]}")

    # Send acknowledgment
    send_message(chat_id, f"🔄 Processing task from @{user}...\n<code>{text[:100]}</code>")

    # Execute task
    result = process_task(text)

    # Format response
    status = "✅ Success" if result["success"] else "❌ Failed"
    output = result["output"][:500] if len(result["output"]) > 500 else result["output"]

    response_text = f"{status}\n\n<pre>{output}</pre>\n\nCode: {result['code']}"

    # Send result
    send_message(chat_id, response_text)

def main():
    """Main polling loop"""
    global last_update_id

    print(f"🤖 Bot started: @Myorbitubot")
    print(f"📍 Token: {BOT_TOKEN[:20]}...")
    print(f"📁 Project: misha-coder.vercel.app")
    print(f"⏳ Listening for messages...\n")

    try:
        while True:
            updates = get_updates()

            for update in updates:
                last_update_id = update["update_id"]

                if "message" in update:
                    try:
                        handle_message(update["message"])
                    except Exception as e:
                        print(f"Error handling message: {e}")
                        chat_id = update["message"]["chat"]["id"]
                        send_message(chat_id, f"❌ Error: {str(e)[:100]}")

    except KeyboardInterrupt:
        print("\n⏹️ Bot stopped")
    except Exception as e:
        print(f"Fatal error: {e}")

if __name__ == "__main__":
    main()
