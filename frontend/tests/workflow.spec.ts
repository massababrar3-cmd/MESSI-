import { test, expect, type Page } from '@playwright/test';
import fs from 'node:fs/promises';
const accounts = JSON.parse(
  await fs.readFile(
    process.env.MESSI_E2E_ACCOUNTS || new URL('../../.local/bootstrap-users.json', import.meta.url),
    'utf8',
  ),
);
async function login(page: Page, role = 'owner') {
  const account = accounts.find((u: any) => u.role === role);
  await page.goto('/');
  await page.getByLabel('Email address').fill(account.email);
  await page.getByLabel('Password', { exact: true }).fill(account.password);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Planning studio', exact: true })).toBeVisible();
  await expect(page.getByLabel('Scenario', { exact: true })).toBeVisible();
}
async function createProject(page: Page, sample = true) {
  await page.getByRole('button', { name: 'New project', exact: true }).click();
  await page.getByLabel('Project name', { exact: true }).fill('E2E synthetic ' + Date.now());
  if (sample) await page.getByLabel('Start with the synthetic 10-block coal example').check();
  await page.getByRole('button', { name: 'Create project', exact: true }).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(page.getByLabel('Scenario', { exact: true })).toBeVisible();
}
async function run(page: Page) {
  await page.getByRole('button', { name: 'Run schedule', exact: true }).click();
  await expect(page.locator('.schedule-panel .badge')).toHaveText('feasible');
  await expect(page.getByText('0 validation violations · feasible')).toBeVisible();
}

test('3D model, inspector, schedule, balanced exports and approval work end to end', async ({
  page,
}) => {
  await login(page);
  await createProject(page);
  const pageErrors: string[] = [];
  page.on('pageerror', (e) => pageErrors.push(e.message));
  await expect(page.getByTestId('mine-canvas')).toBeVisible();
  const graphics = await page
    .getByTestId('mine-canvas')
    .evaluate((canvas: HTMLCanvasElement) => ({ width: canvas.width, height: canvas.height }));
  expect(graphics.width).toBeGreaterThan(100);
  await page.locator('table').getByRole('button', { name: 'CL-001', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'CL-001', exact: true })).toBeVisible();
  await page.getByLabel('Block priority').fill('2');
  await page.getByRole('button', { name: 'Save changes', exact: true }).click();
  await expect(page.getByText('Scenario changes saved.', { exact: false })).toBeVisible();
  await run(page);
  await page.getByLabel('Playback date').fill('2026-11-04');
  await page.evaluate(() => scrollTo(0, 0));
  await page.screenshot({ path: 'test-results/planning-studio.png' });
  await page.getByRole('button', { name: 'Material balance', exact: true }).click();
  await expect(page.locator('.stock-value').filter({ hasText: '112,000' })).toBeVisible();
  await page.getByRole('button', { name: 'Reports & exports', exact: true }).click();
  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('link', { name: 'Schedule CSV', exact: false }).click();
  const download = await downloadPromise;
  const csv = await fs.readFile((await download.path())!, 'utf8');
  expect(csv).toContain('input_hash');
  expect(csv).toContain('coal');
  await page.getByRole('button', { name: 'Approve validated run', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Approved', exact: true })).toBeDisabled();
  expect(pageErrors).toEqual([]);
});

test('invalid CSV is rejected and an analytic ten-block model imports and schedules', async ({
  page,
}) => {
  await login(page);
  await createProject(page, false);
  await page.getByRole('button', { name: 'Import model', exact: true }).click();
  const header = 'id,x,y,z,dx,dy,dz,density,material,basis,destination\n';
  await page
    .getByLabel('Block CSV file')
    .setInputFiles({
      name: 'invalid.csv',
      mimeType: 'text/csv',
      buffer: Buffer.from(header + 'A,0,0,0,-1,10,10,2.5,waste,dry,dump\n'),
    });
  await page.getByRole('button', { name: 'Validate import', exact: true }).click();
  await expect(page.getByText('errors — nothing committed', { exact: false })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Commit import', exact: true })).toBeDisabled();
  const content =
    header +
    Array.from({ length: 10 }, (_, i) => `B${i},${i * 10},0,0,10,10,10,2.5,waste,dry,dump`).join(
      '\n',
    ) +
    '\n';
  await page
    .getByLabel('Block CSV file')
    .setInputFiles({ name: 'ten-blocks.csv', mimeType: 'text/csv', buffer: Buffer.from(content) });
  await page.getByRole('button', { name: 'Validate import', exact: true }).click();
  await expect(page.getByText('10 valid blocks', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Commit import', exact: true }).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(page.locator('.metric').filter({ hasText: 'IN-SITU VOLUME' })).toContainText(
    '10,000',
  );
  await run(page);
  await page.getByRole('button', { name: 'Reports & exports', exact: true }).click();
  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('link', { name: 'Engineering archive', exact: false }).click();
  const d = await downloadPromise;
  const json = JSON.parse(await fs.readFile((await d.path())!, 'utf8'));
  expect(json.result.totals.volume).toBe(10000);
  expect(json.result.totals.tonnes).toBe(25000);
  expect(json.result.violations).toEqual([]);
  expect(json.snapshot.source.original_csv).toBe(content);
});

test('scenario fleet edits leave the baseline immutable and stale results are labelled', async ({
  page,
}) => {
  await login(page);
  await createProject(page);
  await run(page);
  await page.getByRole('button', { name: 'Scenarios', exact: true }).click();
  await page.getByRole('button', { name: 'Branch scenario', exact: true }).click();
  await page.getByLabel('Scenario name', { exact: true }).fill('Reduced waste fleet');
  await page.getByRole('button', { name: 'Create branch', exact: true }).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await page.getByRole('button', { name: 'Fleet & calendars', exact: true }).click();
  await page.getByLabel('Rate ex-01', { exact: true }).fill('2000');
  await page.getByRole('button', { name: 'Save changes', exact: true }).click();
  await page.getByRole('button', { name: 'Planning studio', exact: true }).click();
  await run(page);
  await page.getByLabel('Block priority').fill('8');
  await expect(page.getByText('Inputs changed. The displayed run', { exact: false })).toBeVisible();
  await page.getByRole('button', { name: 'Save changes', exact: true }).click();
  await page.getByRole('button', { name: 'Scenarios', exact: true }).click();
  await page
    .locator('.scenario-card')
    .filter({ has: page.getByRole('heading', { name: 'Baseline plan', exact: true }) })
    .getByRole('button', { name: 'Open scenario', exact: false })
    .click();
  await page.getByRole('button', { name: 'Fleet & calendars', exact: true }).click();
  await expect(page.getByLabel('Rate ex-01', { exact: true })).toHaveValue('4200');
});

test('read-only user can inspect but cannot see editing or scheduling controls', async ({
  page,
}) => {
  await login(page, 'viewer');
  await expect(page.getByRole('button', { name: 'Run schedule', exact: true })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Import model', exact: true })).toHaveCount(0);
  await expect(page.getByLabel('Block priority')).toBeDisabled();
  await page.getByRole('button', { name: 'Fleet & calendars', exact: true }).click();
  await expect(page.getByLabel('Rate ex-01', { exact: true })).toBeDisabled();
  await page.getByRole('button', { name: 'Sign out', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Welcome to MESSI', exact: true })).toBeVisible();
});

test('two tabs expose revision conflicts instead of losing an edit', async ({ page, context }) => {
  await login(page);
  await createProject(page);
  const projectValue = await page.getByLabel('Project', { exact: true }).inputValue();
  const second = await context.newPage();
  await second.goto('/');
  await expect(second.getByLabel('Project', { exact: true })).toBeVisible();
  await second.getByLabel('Project', { exact: true }).selectOption(projectValue);
  await expect(second.getByLabel('Block priority')).toHaveValue('1');
  await page.getByLabel('Block priority').fill('5');
  await page.getByRole('button', { name: 'Save changes', exact: true }).click();
  await expect(page.getByText('Scenario changes saved.', { exact: false })).toBeVisible();
  await second.getByLabel('Block priority').fill('9');
  await second.getByRole('button', { name: 'Save changes', exact: true }).click();
  await expect(second.getByRole('alert')).toContainText('Scenario changed. Reload');
  await second.close();
});

test('small-screen navigation remains usable without horizontal page overflow', async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await login(page);
  await expect(page.getByTestId('mine-canvas')).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.getByRole('button', { name: 'Fleet & calendars', exact: true }).click();
  await expect(page.getByLabel('Rate ex-01', { exact: true })).toBeVisible();
  await page.screenshot({ path: 'test-results/mobile-workspace.png', fullPage: true });
});

test('triangular reference surface imports into the same 3D project without changing block tonnes', async ({
  page,
}) => {
  await login(page);
  await createProject(page);
  await page.getByRole('button', { name: 'Import model', exact: true }).click();
  await page.getByLabel('Model type', { exact: true }).selectOption('surface');
  const obj =
    'v 641980 7489980 232\nv 642220 7489980 232\nv 641980 7490060 232\nv 642220 7490060 232\nf 1 2 3\nf 2 4 3\n';
  await page
    .getByLabel('Block CSV file')
    .setInputFiles({ name: 'survey.obj', mimeType: 'text/plain', buffer: Buffer.from(obj) });
  await page.getByRole('button', { name: 'Validate import', exact: true }).click();
  await expect(page.getByText('2 valid triangles', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Commit import', exact: true }).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(page.getByRole('checkbox', { name: 'Surfaces (1)', exact: true })).toBeChecked();
  await expect(page.locator('.metric').filter({ hasText: 'MODEL COAL' })).toContainText('112,000');
  await page.getByRole('button', { name: 'Cross section', exact: true }).click();
  await expect(page.getByLabel('Section elevation')).toBeVisible();
});

test('signing out in one tab clears private workspace in another tab', async ({
  page,
  context,
}) => {
  await login(page);
  const second = await context.newPage();
  await second.goto('/');
  await expect(second.getByRole('heading', { name: 'Planning studio', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Sign out', exact: true }).click();
  await expect(
    second.getByRole('heading', { name: 'Welcome to MESSI', exact: true }),
  ).toBeVisible();
  await expect(second.getByTestId('mine-canvas')).toHaveCount(0);
  await second.close();
});
