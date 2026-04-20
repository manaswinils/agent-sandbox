/**
 * Puppeteer E2E tests for the motivational quote app.
 * Makes real Anthropic API calls — tests validate actual live behaviour.
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
      pass('/health JSON body is {"status": "ok"}');
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
    pass(`Page title: "${title}"`);
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

async function testRealAnthropicAPICall(page) {
  console.log('\n[e2e] Test: Form submission with live Anthropic API call');
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

  const WORK_DESCRIPTION = 'software engineering';
  await workInput.type(WORK_DESCRIPTION);

  // Real Anthropic API call — Claude can take 3-15s to respond
  try {
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'networkidle0', timeout: 60000 }),
      submitBtn.click(),
    ]);
    pass('Form submitted — Anthropic API call completed');
  } catch (e) {
    fail(`API call timed out or navigation failed (60s limit): ${e.message}`);
    return;
  }

  // ── check for server/API errors ──────────────────────────────────────────

  // .error element in the template means the API call raised an exception
  const errorEl = await page.$('.error');
  if (errorEl) {
    const errorText = await errorEl.evaluate(el => el.innerText.trim());
    fail(`App returned an error message: "${errorText}"`);
    return;
  }
  pass('No .error element — API call did not raise an exception');

  // Generic server error phrases in page body
  const bodyText = await page.evaluate(() => document.body.innerText.trim());
  const lower = bodyText.toLowerCase();
  const errorPhrases = ['internal server error', 'traceback', '500', 'invalid api key', 'authentication error'];
  const found = errorPhrases.find(p => lower.includes(p));
  if (found) {
    fail(`Response body contains error phrase: "${found}"`);
    return;
  }
  pass('No server error phrases in response body');

  // ── validate the quote rendered in .quote-box ────────────────────────────

  const quoteBox = await page.$('.quote-box');
  if (!quoteBox) {
    fail('.quote-box element not present — quote was not rendered');
    return;
  }
  pass('.quote-box element is present');

  const quoteText = await quoteBox.evaluate(el => el.innerText.trim());

  if (quoteText.length === 0) {
    fail('.quote-box is empty — Anthropic returned no content');
    return;
  }
  pass(`Quote is non-empty (${quoteText.length} chars)`);

  if (quoteText.length >= 30) {
    pass(`Quote has substantial length: ${quoteText.length} chars`);
  } else {
    fail(`Quote is suspiciously short (${quoteText.length} chars): "${quoteText}"`);
  }

  // Must contain real words, not just punctuation
  const wordCount = quoteText.split(/\s+/).filter(w => /[a-zA-Z]{2,}/.test(w)).length;
  if (wordCount >= 5) {
    pass(`Quote contains ${wordCount} words`);
  } else {
    fail(`Quote has too few words (${wordCount}): "${quoteText}"`);
  }

  // Log the actual quote so the pipeline output shows what Claude returned
  console.log(`  → Quote text: "${quoteText.substring(0, 120)}${quoteText.length > 120 ? '...' : ''}"`);

  // ── check work label rendered correctly ─────────────────────────────────

  const workLabel = await page.$('.work-label');
  if (workLabel) {
    const labelText = await workLabel.evaluate(el => el.innerText.trim());
    if (labelText.includes(WORK_DESCRIPTION)) {
      pass(`Work label shows submitted input: "${labelText}"`);
    } else {
      fail(`Work label does not contain "${WORK_DESCRIPTION}": "${labelText}"`);
    }
  } else {
    fail('.work-label element not found after successful submission');
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
    // No navigation = HTML5 required validation blocked submit — acceptable
  }

  if (navigated) {
    const bodyText = await page.evaluate(() => document.body.innerText.trim());
    const lower = bodyText.toLowerCase();
    if (lower.includes('traceback') || lower.includes('internal server error')) {
      fail('Empty form submission caused a server error');
    } else {
      pass('Empty form submission handled without server error');
    }
    // No .quote-box should appear for empty input
    const quoteBox = await page.$('.quote-box');
    if (!quoteBox) {
      pass('No .quote-box rendered for empty submission (correct)');
    } else {
      const quoteText = await quoteBox.evaluate(el => el.innerText.trim());
      if (quoteText.length > 0) {
        fail('Quote was rendered despite empty input');
      }
    }
  } else {
    pass('Empty form blocked by HTML5 required validation (no navigation)');
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
  if (res.status() === 500) {
    fail('Unmatched route returned HTTP 500 instead of 404');
  } else {
    pass(`Unmatched route returned HTTP ${res.status()} (not 500)`);
  }
}

// ── runner ────────────────────────────────────────────────────────────────────

(async () => {
  console.log(`\n[e2e] Starting E2E tests against: ${BASE_URL}`);
  console.log(`[e2e] Note: testRealAnthropicAPICall makes a live Anthropic API call\n`);

  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu'],
  });

  const page = await browser.newPage();
  page.setDefaultTimeout(60000);

  const jsErrors = [];
  page.on('pageerror', err => jsErrors.push(err.message));
  page.on('response', res => {
    if (res.status() >= 500) {
      issues.push(`Server returned HTTP ${res.status()} for ${res.url()}`);
    }
  });

  try {
    await testHealthEndpoint(page);
    await testMainPageStructure(page);
    await testRealAnthropicAPICall(page);
    await testEmptyFormSubmission(page);
    await testNotFoundPage(page);
  } catch (err) {
    issues.push(`Test runner error: ${err.message}`);
  } finally {
    await browser.close();
  }

  if (jsErrors.length > 0) {
    jsErrors.forEach(e => fail(`Browser JS error: ${e}`));
  }

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
