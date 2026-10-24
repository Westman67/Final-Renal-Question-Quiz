import {test, expect} from '@playwright/test';

const PATHOLOGY_PREFERENCES = 'renal-pathology-picture-quiz-preferences-v2';
const PHYSIOLOGY_PREFERENCES = 'renal-picture-quiz-preferences-v2';

function watchForBrowserFailures(page) {
  const failures = [];
  page.on('console', message => {
    if (message.type() === 'error') failures.push(`console: ${message.text()}`);
  });
  page.on('pageerror', error => failures.push(`page: ${error.message}`));
  page.on('requestfailed', request => failures.push(`request: ${request.url()} ${request.failure()?.errorText || ''}`));
  page.on('response', response => {
    if (response.status() >= 400) failures.push(`response: ${response.status()} ${response.url()}`);
  });
  return failures;
}

async function resetAndOpen(page, path = '') {
  await page.goto(path || './');
  await page.evaluate(() => localStorage.clear());
  await page.reload();
  await expect(page.getByRole('heading', {name: 'Choose your practice'})).toBeVisible();
}

async function openPathologyCollection(page, collection) {
  await page.addInitScript(({key, collection}) => {
    localStorage.clear();
    localStorage.setItem('renal-picture-quiz-bank-selection-v2', 'pathology');
    localStorage.setItem(key, JSON.stringify({
      schema_version: 1,
      category: 'all',
      difficulty: 'all',
      reasoning_type: 'all',
      collection: [collection],
      filter: 'all',
      mode: 'learn',
      length: 'all',
    }));
  }, {key: PATHOLOGY_PREFERENCES, collection});
  await page.goto('?bank=pathology');
  await expect(page.getByRole('heading', {name: 'Choose your practice'})).toBeVisible();
}

async function openPhysiologyCollection(page, collection) {
  await page.addInitScript(({key, collection}) => {
    localStorage.clear();
    localStorage.setItem('renal-picture-quiz-bank-selection-v2', 'physiology');
    localStorage.setItem(key, JSON.stringify({
      schema_version: 1,
      category: 'all',
      difficulty: 'all',
      reasoning_type: 'all',
      collection: [collection],
      filter: 'all',
      mode: 'learn',
      length: 'all',
    }));
  }, {key: PHYSIOLOGY_PREFERENCES, collection});
  await page.goto('?bank=physiology');
  await expect(page.getByRole('heading', {name: 'Choose your practice'})).toBeVisible();
}

test('visible naming, metadata filters, and keyboard navigation work', async ({page}) => {
  const failures = watchForBrowserFailures(page);
  await resetAndOpen(page);
  await expect(page).toHaveTitle(/Visual Questions/);
  await expect(page.locator('.brand-sub')).toContainText('VISUAL QUESTIONS');
  await expect(page.getByLabel('Difficulty')).toBeVisible();
  await expect(page.getByLabel('Reasoning type')).toBeVisible();
  await page.getByLabel('Difficulty').selectOption('advanced');
  await page.getByLabel('Reasoning type').selectOption('mechanism');
  await expect(page.getByRole('button', {name: /Start/})).toBeEnabled();
  await page.getByRole('button', {name: /Start/}).click();
  await expect(page.locator('.quiz-meta')).toContainText('1 /');
  await page.keyboard.press('ArrowRight');
  await expect(page.locator('.quiz-meta')).toContainText('2 /');
  await page.keyboard.press('ArrowLeft');
  await expect(page.locator('.quiz-meta')).toContainText('1 /');
  expect(failures).toEqual([]);
});

test('Learn reveals feedback while Exam defers it', async ({page}) => {
  const failures = watchForBrowserFailures(page);
  await resetAndOpen(page);
  await page.getByRole('button', {name: /Start/}).click();
  await page.locator('[data-choice]').first().click();
  await page.getByRole('button', {name: 'Submit answer'}).click();
  await expect(page.getByRole('heading', {name: 'Every option explained'})).toBeVisible();

  await resetAndOpen(page);
  await page.getByLabel('Exam').check();
  await page.getByRole('button', {name: /Start/}).click();
  await page.locator('[data-choice]').first().click();
  await page.getByRole('button', {name: 'Submit answer'}).click();
  await expect(page.getByText('Feedback appears after the exam.')).toBeVisible();
  await expect(page.locator('#feedback')).toHaveCount(0);
  expect(failures).toEqual([]);
});

test('primary source-grounded tables render', async ({page}) => {
  const failures = watchForBrowserFailures(page);
  await openPathologyCollection(page, 'R35');
  await page.getByRole('button', {name: /Start 4 questions/}).click();
  await expect(page.getByLabel('Primary case data')).toBeVisible();
  expect(failures).toEqual([]);
});

test('R30 includes four explicit table-based RTA profiles', async ({page}) => {
  const failures = watchForBrowserFailures(page);
  await openPathologyCollection(page, 'R30');
  await page.getByRole('button', {name: /Start 5 questions/}).click();
  let tableQuestions = 0;
  for (let index = 0; index < 5; index += 1) {
    if (await page.getByLabel('Primary case data').count()) {
      tableQuestions += 1;
      await expect(page.locator('.quiz-layout')).toHaveClass(/table-only/);
    }
    if (index < 4) await page.keyboard.press('ArrowRight');
  }
  expect(tableQuestions).toBe(4);
  expect(failures).toEqual([]);
});

test('additional case context appears in the R34 session', async ({page}) => {
  const failures = watchForBrowserFailures(page);
  await openPathologyCollection(page, 'R34');
  await page.getByRole('button', {name: /Start 14 questions/}).click();
  let found = false;
  for (let index = 0; index < 14; index += 1) {
    if (await page.getByLabel('Additional case context').count()) {
      found = true;
      break;
    }
    await page.keyboard.press('ArrowRight');
  }
  expect(found).toBe(true);
  expect(failures).toEqual([]);
});

test('table-only cases render without image tools and keep arrow navigation', async ({page}) => {
  const failures = watchForBrowserFailures(page);
  await openPathologyCollection(page, 'R27');
  await page.getByRole('button', {name: /Start 22 questions/}).click();
  await expect(page.getByLabel('Primary case data')).toBeVisible();
  await expect(page.locator('.quiz-layout')).toHaveClass(/table-only/);
  await expect(page.locator('#quiz-image')).toHaveCount(0);
  await expect(page.getByRole('button', {name: 'Flag image'})).toHaveCount(0);
  await page.keyboard.press('ArrowRight');
  await expect(page.locator('.quiz-meta')).toContainText('2 / 22');
  await page.keyboard.press('ArrowLeft');
  await expect(page.locator('.quiz-meta')).toContainText('1 / 22');
  expect(failures).toEqual([]);
});

test('mobile layout puts the prompt before the image', async ({page}) => {
  const failures = watchForBrowserFailures(page);
  await page.setViewportSize({width: 390, height: 844});
  await openPhysiologyCollection(page, 'R1');
  await page.getByRole('button', {name: /Start/}).click();
  const firstClass = await page.locator('.quiz-layout').evaluate(element => element.firstElementChild?.className);
  expect(firstClass).toContain('question-prompt');
  await expect(page.locator('#quiz-image')).toBeVisible();
  expect(failures).toEqual([]);
});

test('image flags save through the in-app form and appear in Source review', async ({page}) => {
  const failures = watchForBrowserFailures(page);
  await openPhysiologyCollection(page, 'R1');
  await page.getByRole('button', {name: /Start/}).click();
  await page.getByRole('button', {name: 'Flag image'}).click();
  await expect(page.getByRole('heading', {name: 'Flag this image'})).toBeVisible();
  await page.getByLabel('Image issue').fill('The arrow label is difficult to distinguish.');
  await page.getByRole('button', {name: 'Save image flag'}).click();
  await expect(page.getByRole('button', {name: 'Image flagged'})).toBeVisible();
  await page.getByRole('button', {name: 'Source review'}).click();
  await expect(page.getByText('The arrow label is difficult to distinguish.')).toBeVisible();
  await expect(page.getByRole('button', {name: '1 open image flags'})).toBeVisible();
  expect(failures).toEqual([]);
});
