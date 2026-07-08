const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  const fileUrl = 'file://' + path.resolve(__dirname, 'index.html').replace(/\\/g, '/');
  await page.goto(fileUrl, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);
  const title = await page.title();
  console.log('Page title:', title);
  await page.screenshot({ path: 'screenshots/site-full.png', fullPage: true });
  await page.screenshot({ path: 'screenshots/site-view.png' });
  console.log('Screenshots saved.');
  await browser.close();
})();
