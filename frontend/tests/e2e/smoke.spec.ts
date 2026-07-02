import { expect, test } from '@playwright/test';

test('operator can navigate the live MVP workspaces', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Fleet overview.' })).toBeVisible();

  await page.getByRole('link', { name: 'Fleet / Robots' }).click();
  await expect(page.getByRole('heading', { name: 'Robots' })).toBeVisible();
  await expect(page.getByText('RB-SIM-001').first()).toBeVisible();

  await page.getByRole('link', { name: 'Map & Routes' }).click();
  await expect(page.getByRole('heading', { name: 'Map & Routes' })).toBeVisible();

  await page.getByRole('link', { name: 'Missions' }).click();
  await expect(page.getByRole('heading', { name: 'Missions' })).toBeVisible();
  await page.getByRole('link', { name: 'Monitor' }).first().click();
  await expect(page.getByRole('heading', { name: 'Mission monitor' })).toBeVisible();
  await expect(page.getByText(/\d+ position samples/)).toBeVisible();
  await page.getByRole('button', { name: 'Start replay' }).click();
  await expect(page.getByText('Replay', { exact: true })).toBeVisible();

  await page.getByRole('link', { name: 'MQTT / VDA Logs' }).click();
  await expect(page.getByRole('heading', { name: 'MQTT / VDA Logs' })).toBeVisible();
  await expect(page.locator('tbody').getByText('state', { exact: true }).first()).toBeVisible();
  await page.getByRole('button', { name: 'Inspect' }).first().click();
  await expect(page.getByText('Schema valid')).toBeVisible();
});
