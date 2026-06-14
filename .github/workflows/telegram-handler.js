const axios = require('axios');
const fs = require('fs');
const path = require('path');

const BOT_TOKEN = process.env.BOT_TOKEN || "8598513999:AAFhhzutC-6CNon6olbozTsPQgedNYneKp0";
const TELEGRAM_API = `https://api.telegram.org/bot${BOT_TOKEN}`;
const STATE_FILE = path.join(process.cwd(), '.github/bot-state.json');
const MESSAGES_FILE = path.join(process.cwd(), 'bot-messages.json');

const MAX_RETRIES = 5;

let lastUpdateId = 0;

function log(msg) {
  console.log(`[${new Date().toISOString()}] ${msg}`);
}

// Escape text before putting it inside an HTML parse_mode message,
// otherwise '<', '>' or '&' in user input makes Telegram reject the
// request with HTTP 400 and the message silently fails to send.
function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function loadState() {
  try {
    if (fs.existsSync(STATE_FILE)) {
      const data = JSON.parse(fs.readFileSync(STATE_FILE, 'utf8'));
      lastUpdateId = data.lastUpdateId || 0;
      log(`Loaded state: lastUpdateId=${lastUpdateId}`);
    }
  } catch (e) {
    log('State file not found, starting fresh');
  }
}

function saveState() {
  fs.mkdirSync(path.dirname(STATE_FILE), { recursive: true });
  fs.writeFileSync(STATE_FILE, JSON.stringify({ lastUpdateId }, null, 2));
  log(`Saved state: lastUpdateId=${lastUpdateId}`);
}

function loadMessages() {
  try {
    if (fs.existsSync(MESSAGES_FILE)) {
      return JSON.parse(fs.readFileSync(MESSAGES_FILE, 'utf8'));
    }
  } catch (e) {
    log(`Error loading messages: ${e.message}`);
  }
  return [];
}

async function getUpdates() {
  for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
    try {
      const response = await axios.get(`${TELEGRAM_API}/getUpdates`, {
        params: {
          offset: lastUpdateId + 1,
          timeout: 25,
          allowed_updates: JSON.stringify(['message'])
        },
        timeout: 30000
      });

      if (response.data.ok) {
        const updates = response.data.result || [];
        log(`Fetched ${updates.length} update(s)`);
        return updates;
      }
      log(`API returned not ok: ${response.data.description}`);
    } catch (error) {
      const reason = error.response?.data?.description || error.code || error.message;
      log(`getUpdates attempt ${attempt}/${MAX_RETRIES} failed: ${reason}`);
      if (attempt < MAX_RETRIES) {
        await new Promise(r => setTimeout(r, Math.pow(2, attempt) * 1000));
      }
    }
  }
  return null; // null => fetch failed, do not advance the offset
}

// Tell Telegram we have consumed everything up to lastUpdateId.
// This is what actually makes reading idempotent: once confirmed,
// Telegram will not return these updates again, even on a fresh
// runner where the state file did not survive.
async function confirmUpdates() {
  try {
    await axios.get(`${TELEGRAM_API}/getUpdates`, {
      params: { offset: lastUpdateId + 1, timeout: 0 },
      timeout: 15000
    });
    log(`Confirmed updates up to ${lastUpdateId}`);
  } catch (error) {
    log(`Failed to confirm updates: ${error.message}`);
  }
}

async function sendMessage(chatId, text) {
  try {
    const response = await axios.post(`${TELEGRAM_API}/sendMessage`, {
      chat_id: chatId,
      text: text,
      parse_mode: 'HTML'
    }, { timeout: 10000 });
    return response.data;
  } catch (error) {
    const reason = error.response?.data?.description || error.message;
    log(`Error sending message: ${reason}`);
    return null;
  }
}

async function processUpdates() {
  const updates = await getUpdates();

  if (updates === null) {
    log('Could not fetch updates, skipping this run');
    return;
  }

  if (updates.length === 0) {
    log('No updates');
    return;
  }

  const messages = loadMessages();
  const known = new Set(messages.map(m => m.id));
  let newCount = 0;

  for (const update of updates) {
    if (update.update_id > lastUpdateId) {
      lastUpdateId = update.update_id;
    }

    if (!update.message || known.has(update.update_id)) {
      continue;
    }

    const message = update.message;
    const chatId = message.chat.id;
    const text = message.text || '';
    const userId = message.from.username || `user_${message.from.id}`;

    log(`Message from @${userId} (chat ${chatId}): ${text}`);

    messages.push({
      id: update.update_id,
      timestamp: new Date().toISOString(),
      userId,
      chatId,
      text,
      processed: false
    });
    known.add(update.update_id);
    newCount++;

    await sendMessage(
      chatId,
      `🔄 Задание получено от @${escapeHtml(userId)}\n<code>${escapeHtml(text.substring(0, 200))}</code>`
    );
  }

  fs.writeFileSync(MESSAGES_FILE, JSON.stringify(messages, null, 2));
  log(`Stored ${newCount} new message(s)`);

  // Persist progress both ways: locally (fallback) and to Telegram (authoritative).
  saveState();
  await confirmUpdates();
}

async function main() {
  log('🤖 Telegram Handler Started');
  log(`Token: ${BOT_TOKEN.substring(0, 12)}...`);

  loadState();
  await processUpdates();

  log('✅ Handler completed');
}

main().catch(err => {
  console.error('Fatal error:', err.message);
  process.exit(1);
});
