/**
 * Puppeteer E2E tests for the motivational quote app.
 *
 * Usage:
 *   node test_e2e.js <base_url>
 *
 * Exit codes:
 *   0 — all tests passed
 *   1 — one or more tests failed (issues printed to stderr)
 */

const puppeteer = require('puppeteer');

const BASE_URL = process.argv[2];
if (!BASE_URL) {
  console.error('Usage: node test_e2e.js <base_url>');
  process.exit(1);
}

const issues = [];
let passed = 0;

function pass(msg) {
  console.log(`  ✓ ${msg}`);
  passed++;
}

function fail(msg) {
  console.error(`  ✗ ${msg}`);
  issues.push(msg);
}

// ── tests ─────────────────────────────────────────────────────────────────────

async function testHealthEndpoint(page) {
  console.log('\n[e2e] Test: /health endpoint');
  let res;
  try {
    res = await page.goto(`${BASE_URL}/health`, { waitUntil: 'networkidle0', timeout: 15000 });
  } catch (e) {
    fail(`/health navigation failed: ${e.message}`);
    return;
  }

  if (res.status() === 200) {
    pass('/health returned HTTP 200');
  } else {
    fail(`/health returned HTTP ${res.status()}, expected 200`);
    return;
  }

  try {
    const text = await page.evaluate(() => document.body.innerText.trim());
    const data = JSON.parse(text);
    if (data.status === 'ok') {
      pass('/health JSON body contains {"status": "ok"}');
    } else {
      fail(`/health JSON status is "${data.status}", expected "ok"`);
    }
  } catch (e) {
    fail(`/health response is not valid JSON: ${e.message}`);
  }
}

async function testMainPageStructure(page) {
  console.log('\n[e2e] Test: Main page structure');
  let res;
  try {
    res = await page.goto(BASE_URL, { waitUntil: 'networkidle0', timeout: 15000 });
  } catch (e) {
    fail(`Main page navigation failed: ${e.message}`);
    return;
  }

  if (res.status() === 200) {
    pass('Main page returned HTTP 200');
  } else {
    fail(`Main page returned HTTP ${res.status()}, expected 200`);
    return;
  }

  const title = await page.title();
  if (title && title.trim().length > 0) {
    pass(`Page has a title: "${title}"`);
  } else {
    fail('Page title is empty');
  }

  const form = await page.$('form');
  if (form) {
    pass('<form> element present');
  } else {
    fail('No <form> element found on main page');
    return;
  }

  const workInput = await page.$('input[name="work"], textarea[name="work"]');
  if (workInput) {
    pass('Work input field (name="work") present');
  } else {
    fail('No input or textarea with name="work" found');
  }

  const submitBtn = await page.$('button[type="submit"], input[type="submit"], button:not([type])');
  if (submitBtn) {
    pass('Submit button present');
  } else {
    fail('No submit button found');
  }
}

async function testValidFormSubmission(page) {
  console.log('\n[e2e] Test: Form submission with valid input');
  try {
    await page.goto(BASE_URL, { waitUntil: 'networkidle0', timeout: 15000 });
  } catch (e) {
    fail(`Navigation to main page failed: ${e.message}`);
    return;
  }

  const workInput = await page.$('input[name="work"], textarea[name="work"]');
  if (!workInput) {
    fail('Cannot test form — work input not found');
    return;
  }

  const submitBtn = await page.$('button[type="submit"], input[type="submit"], button:not([type])');
  if (!submitBtn) {
    fail('Cannot test form — submit button not found');
    return;
  }

  await workInput.type('software engineering');

  try {
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'networkidle0', timeout: 30000 }),
      submitBtn.click(),
    ]);
    pass('Form submitted (navigation completed)');
  } catch (e) {
    fail(`Form submission timed out or failed: ${e.message}`);
    return;
  }

  const bodyText = await page.evaluate(() => document.body.innerText.trim());
  if (bodyText.length > 80) {
    pass(`Response has content (${bodyText.length} chars)`);
  } else {
    fail(`Response body is too short (${bodyText.length} chars) — may indicate an error`);
  }

  const lower = bodyText.toLowerCase();
  const errorIndicators = ['internal server error', 'traceback', 'exception', '500'];
  const foundError = errorIndicators.find(e => lower.includes(e));
  if (foundError) {
    fail(`Response contains server error indicator: "${foundError}"`);
  } else {
    pass('Response does not contain server error indicators');
  }
}

async function testEmptyFormSubmission(page) {
  console.log('\n[e2e] Test: Form submission with empty input');
  try {
    await page.goto(BASE_URL, { waitUntil: 'networkidle0', timeout: 15000 });
  } catch (e) {
    fail(`Navigation to main page failed: ${e.message}`);
    return;
  }

  const submitBtn = await page.$('button[type="submit"], input[type="submit"], button:not([type])');
  if (!submitBtn) {
    fail('Cannot test empty form — submit button not found');
    return;
  }

  let navigated = false;
  try {
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'networkidle0', timeout: 5000 }),
      submitBtn.click(),
    ]);
    navigated = true;
  } catch (_) {
    // No navigation = client-side validation blocked submit — that's acceptable
  }

  if (navigated) {
    const bodyText = await page.evaluate(() => document.body.innerText.trim());
    const lower = bodyText.toLowerCase();
    if (lower.includes('traceback') || lower.includes('internal server error')) {
      fail('Empty form submission caused a server error');
    } else {
      pass('Empty form submission handled without server error');
    }
    if (lower.includes('500')) {
      fail('Empty form submission returned HTTP 500 content');
    } else {
      pass('No 500 error on empty submission');
    }
  } else {
    pass('Empty form submission blocked by client-side validation');
  }
}

async function testNotFoundPage(page) {
  console.log('\n[e2e] Test: 404 handling');
  let res;
  try {
    res = await page.goto(`${BASE_URL}/nonexistent-route-xyz`, { waitUntil: 'networkidle0', timeout: 10000 });
  } catch (e) {
    fail(`404 test navigation failed: ${e.message}`);
    return;
  }
  // 404 is expected; what we don't want is a 500
  if (res.status() === 500) {
    fail('Unmatched route returned HTTP 500 instead of 404');
  } else {
    pass(`Unmatched route returned HTTP ${res.status()} (not 500)`);
  }
}

// ── runner ────────────────────────────────────────────────────────────────────

(async () => {
  console.log(`\n[e2e] Starting E2E tests against: ${BASE_URL}`);

  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu'],
  });

  const page = await browser.newPage();
  page.setDefaultTimeout(30000);

  // Capture browser-side JS errors
  const jsErrors = [];
  page.on('pageerror', err => jsErrors.push(err.message));

  // Flag unexpected 5xx from the server
  page.on('response', res => {
    if (res.status() >= 500) {
      issues.push(`Server returned HTTP ${res.status()} for ${res.url()}`);
    }
  });

  try {
    await testHealthEndpoint(page);
    await testMainPageStructure(page);
    await testValidFormSubmission(page);
    await testEmptyFormSubmission(page);
    await testNotFoundPage(page);
  } catch (err) {
    issues.push(`Unexpected test runner error: ${err.message}`);
  } finally {
    await browser.close();
  }

  // Report JS errors caught during tests
  if (jsErrors.length > 0) {
    jsErrors.forEach(e => fail(`Browser JS error: ${e}`));
  }

  // Summary
  const total = passed + issues.length;
  console.log(`\n[e2e] Results: ${passed}/${total} passed, ${issues.length} failed`);

  if (issues.length > 0) {
    console.error('\n=== E2E ISSUES ===');
    issues.forEach((issue, i) => console.error(`  [${i + 1}] ${issue}`));
    console.error('==================\n');
    process.exit(1);
  }

  console.log('\n✅ All E2E tests passed\n');
  process.exit(0);
})();
