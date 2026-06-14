const axios = require('axios');
const fs = require('fs');
const path = require('path');

const BOT_TOKEN = process.env.BOT_TOKEN || "8598513999:AAFhhzutC-6CNon6olbozTsPQgedNYneKp0";
const TELEGRAM_API = `https://api.telegram.org/bot${BOT_TOKEN}`;
const RESULTS_FILE = path.join(process.cwd(), 'bot-results.json');

async function sendMessage(chatId, text) {
  try {
    const response = await axios.post(`${TELEGRAM_API}/sendMessage`, {
      chat_id: chatId,
      text: text,
      parse_mode: 'HTML'
    }, {
      timeout: 10000
    });
    return response.data;
  } catch (error) {
    console.log(`Error sending message: ${error.message}`);
    return null;
  }
}

async function sendResults() {
  try {
    if (!fs.existsSync(RESULTS_FILE)) {
      console.log('No results file');
      return;
    }

    const results = JSON.parse(fs.readFileSync(RESULTS_FILE, 'utf8'));

    for (const result of results) {
      if (!result.sent) {
        const status = result.success ? '✅ Success' : '❌ Failed';
        const output = result.output.substring(0, 1000);
        const text = `<b>${status}</b>\n\n<pre>${output}</pre>\n\nCode: ${result.code}`;

        console.log(`Sending result for message ${result.id} to chat ${result.chatId}`);
        const sent = await sendMessage(result.chatId, text);

        if (sent) {
          result.sent = true;
          result.sentAt = new Date().toISOString();
          console.log(`✅ Result sent for message ${result.id}`);
        }
      }
    }

    fs.writeFileSync(RESULTS_FILE, JSON.stringify(results, null, 2));
  } catch (e) {
    console.log(`Error in send-results: ${e.message}`);
  }
}

console.log('📤 Sending results...');
sendResults().then(() => {
  console.log('✅ Send results completed');
}).catch(console.error);
