const axios = require('axios');
const fs = require('fs');
const path = require('path');

const BOT_TOKEN = process.env.BOT_TOKEN || "8598513999:AAFhhzutC-6CNon6olbozTsPQgedNYneKp0";
const TELEGRAM_API = `https://api.telegram.org/bot${BOT_TOKEN}`;
const STATE_FILE = path.join(process.cwd(), '.github/bot-state.json');
const MESSAGES_FILE = path.join(process.cwd(), 'bot-messages.json');
const RESULTS_FILE = path.join(process.cwd(), 'bot-results.json');

let lastUpdateId = 0;

function loadState() {
  try {
    if (fs.existsSync(STATE_FILE)) {
      const data = JSON.parse(fs.readFileSync(STATE_FILE, 'utf8'));
      lastUpdateId = data.lastUpdateId || 0;
    }
  } catch (e) {
    console.log('State file not found, starting fresh');
  }
}

function saveState() {
  fs.mkdirSync(path.dirname(STATE_FILE), { recursive: true });
  fs.writeFileSync(STATE_FILE, JSON.stringify({ lastUpdateId }, null, 2));
}

async function getUpdates() {
  try {
    const response = await axios.get(`${TELEGRAM_API}/getUpdates`, {
      params: {
        offset: lastUpdateId + 1,
        timeout: 30
      }
    });

    if (response.data.ok) {
      return response.data.result || [];
    }
    return [];
  } catch (error) {
    console.log(`Error getting updates: ${error.message}`);
    return [];
  }
}

async function sendMessage(chatId, text) {
  try {
    const response = await axios.post(`${TELEGRAM_API}/sendMessage`, {
      chat_id: chatId,
      text: text,
      parse_mode: 'HTML'
    });
    return response.data;
  } catch (error) {
    console.log(`Error sending message: ${error.message}`);
    return null;
  }
}

async function processUpdates() {
  const updates = await getUpdates();

  if (updates.length === 0) {
    console.log('No updates');
    return;
  }

  for (const update of updates) {
    lastUpdateId = update.update_id;

    if (update.message) {
      const message = update.message;
      const chatId = message.chat.id;
      const text = message.text || '';
      const userId = message.from.username || message.from.id;

      console.log(`[${new Date().toISOString()}] Message from @${userId}: ${text.substring(0, 100)}`);

      // Save message to file
      let messages = [];
      try {
        if (fs.existsSync(MESSAGES_FILE)) {
          messages = JSON.parse(fs.readFileSync(MESSAGES_FILE, 'utf8'));
        }
      } catch (e) {
        messages = [];
      }

      messages.push({
        id: update.update_id,
        timestamp: new Date().toISOString(),
        userId,
        chatId,
        text,
        processed: false
      });

      fs.writeFileSync(MESSAGES_FILE, JSON.stringify(messages, null, 2));

      // Send acknowledgment
      await sendMessage(chatId, `🔄 Задание получено от @${userId}\n<code>${text.substring(0, 100)}</code>`);
    }
  }

  saveState();
}

async function checkResults() {
  try {
    if (fs.existsSync(RESULTS_FILE)) {
      const results = JSON.parse(fs.readFileSync(RESULTS_FILE, 'utf8'));

      for (const result of results) {
        if (!result.sent) {
          const status = result.success ? '✅ Success' : '❌ Failed';
          const output = result.output.substring(0, 500);
          const text = `${status}\n\n<pre>${output}</pre>\n\nCode: ${result.code}`;

          const sent = await sendMessage(result.chatId, text);
          if (sent) {
            result.sent = true;
            result.sentAt = new Date().toISOString();
          }
        }
      }

      fs.writeFileSync(RESULTS_FILE, JSON.stringify(results, null, 2));
    }
  } catch (e) {
    console.log(`Error checking results: ${e.message}`);
  }
}

async function main() {
  console.log('🤖 Telegram Handler Started');
  console.log(`📍 Token: ${BOT_TOKEN.substring(0, 20)}...`);

  loadState();
  await processUpdates();
  await checkResults();

  console.log('✅ Handler completed');
}

main().catch(console.error);
