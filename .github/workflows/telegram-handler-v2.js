const axios = require('axios');
const fs = require('fs');
const path = require('path');

const BOT_TOKEN = "8598513999:AAFhhzutC-6CNon6olbozTsPQgedNYneKp0";
const TELEGRAM_API = `https://api.telegram.org/bot${BOT_TOKEN}`;
const STATE_FILE = path.join(process.cwd(), '.github/bot-state.json');
const MESSAGES_FILE = path.join(process.cwd(), 'bot-messages.json');

let lastUpdateId = 0;
let retryCount = 0;
const MAX_RETRIES = 5;

function log(msg) {
  const time = new Date().toISOString().split('T')[1].split('.')[0];
  console.log(`[${time}] ${msg}`);
}

function loadState() {
  try {
    if (fs.existsSync(STATE_FILE)) {
      const data = JSON.parse(fs.readFileSync(STATE_FILE, 'utf8'));
      lastUpdateId = data.lastUpdateId || 0;
      log(`✅ Loaded state: lastUpdateId=${lastUpdateId}`);
    }
  } catch (e) {
    log('⚠️  State file not found');
  }
}

function saveState() {
  fs.mkdirSync(path.dirname(STATE_FILE), { recursive: true });
  fs.writeFileSync(STATE_FILE, JSON.stringify({ lastUpdateId }, null, 2));
  log(`💾 State saved: lastUpdateId=${lastUpdateId}`);
}

async function getUpdatesWithRetry() {
  for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
    try {
      log(`📡 Fetching updates (attempt ${attempt}/${MAX_RETRIES})...`);

      const response = await axios.get(`${TELEGRAM_API}/getUpdates`, {
        params: {
          offset: lastUpdateId + 1,
          timeout: 10
        },
        timeout: 15000
      });

      if (response.data.ok) {
        const updates = response.data.result || [];
        log(`✅ Got ${updates.length} update(s)`);
        retryCount = 0;
        return updates;
      } else {
        log(`❌ API error: ${response.data.description}`);
      }
    } catch (error) {
      const msg = error.response?.status || error.code || error.message;
      log(`⚠️  Attempt ${attempt} failed: ${msg}`);

      if (attempt < MAX_RETRIES) {
        const waitTime = Math.pow(2, attempt) * 1000;
        log(`⏳ Waiting ${waitTime}ms before retry...`);
        await new Promise(r => setTimeout(r, waitTime));
      }
    }
  }

  log('❌ All retries failed');
  return [];
}

function loadMessages() {
  try {
    if (fs.existsSync(MESSAGES_FILE)) {
      return JSON.parse(fs.readFileSync(MESSAGES_FILE, 'utf8'));
    }
  } catch (e) {
    log(`⚠️  Error loading messages: ${e.message}`);
  }
  return [];
}

function saveMessages(messages) {
  fs.writeFileSync(MESSAGES_FILE, JSON.stringify(messages, null, 2));
  log(`💾 Saved ${messages.length} messages`);
}

async function processUpdates() {
  const updates = await getUpdatesWithRetry();

  if (updates.length === 0) {
    log('📭 No updates');
    return;
  }

  let messages = loadMessages();

  for (const update of updates) {
    lastUpdateId = update.update_id;

    if (update.message) {
      const message = update.message;
      const chatId = message.chat.id;
      const text = message.text || '';
      const userId = message.from.username || `user_${message.from.id}`;

      log(`📬 NEW MESSAGE from @${userId}: "${text.substring(0, 50)}..."`);

      messages.push({
        id: update.update_id,
        timestamp: new Date().toISOString(),
        userId,
        chatId,
        text,
        processed: false
      });
    }
  }

  saveMessages(messages);
  saveState();
}

async function main() {
  log('🚀 Telegram Handler V2 Started');
  log(`📍 Token: ${BOT_TOKEN.substring(0, 20)}...`);
  log(`📡 API: ${TELEGRAM_API}`);

  loadState();
  await processUpdates();

  log('✅ Check completed');
}

main().catch(err => {
  console.error('Fatal error:', err.message);
  process.exit(1);
});
