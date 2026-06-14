const axios = require('axios');

const BOT_TOKEN = "8598513999:AAFhhzutC-6CNon6olbozTsPQgedNYneKp0";
const TELEGRAM_API = `https://api.telegram.org/bot${BOT_TOKEN}`;

console.log("="*60);
console.log("TELEGRAM API TEST REQUEST");
console.log("="*60);

// Запрос который шлется
console.log("\n📤 REQUEST DETAILS:");
console.log("─".repeat(60));
console.log(`Method: GET`);
console.log(`URL: ${TELEGRAM_API}/getUpdates`);
console.log(`Params:`);
console.log(`  - offset: 1`);
console.log(`  - timeout: 10`);
console.log(`Headers:`);
console.log(`  - User-Agent: axios`);

// Попытка отправить
console.log("\n📡 SENDING REQUEST...\n");

axios.get(`${TELEGRAM_API}/getUpdates`, {
  params: {
    offset: 1,
    timeout: 10
  }
})
.then(response => {
  console.log("✅ SUCCESS RESPONSE:");
  console.log("─".repeat(60));
  console.log(`Status: ${response.status}`);
  console.log(`Status Text: ${response.statusText}`);
  console.log(`Headers:`);
  Object.entries(response.headers).forEach(([k, v]) => {
    console.log(`  ${k}: ${v}`);
  });
  console.log(`\nBody:`);
  console.log(JSON.stringify(response.data, null, 2));
})
.catch(error => {
  console.log("❌ ERROR RESPONSE:");
  console.log("─".repeat(60));
  if (error.response) {
    console.log(`Status: ${error.response.status}`);
    console.log(`Status Text: ${error.response.statusText}`);
    console.log(`Message: ${error.message}`);
    console.log(`Headers:`);
    Object.entries(error.response.headers).forEach(([k, v]) => {
      console.log(`  ${k}: ${v}`);
    });
    console.log(`\nResponse Body:`);
    console.log(JSON.stringify(error.response.data, null, 2));
  } else if (error.request) {
    console.log(`No response received`);
    console.log(`Request: ${error.request}`);
    console.log(`Message: ${error.message}`);
  } else {
    console.log(`Error: ${error.message}`);
  }
});
