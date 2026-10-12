import { test, expect } from '@playwright/test';

/**
 * Connected UI smoke test using a throwaway user and synthetic market data.
 * Both the Next.js frontend and the FastAPI backend must be running.
 */
test('signup, market context, demo trade, journal and AI Coach remain connected', async ({ page }) => {
  const email = `e2e-${Date.now()}-${Math.floor(Math.random()*1_000_000)}@example.org`;

  await page.goto('/signup');
  await page.getByLabel('Full name').fill('Investor Demo');
  await page.getByLabel('Email address').fill(email);
  await page.getByLabel('Password').fill('PipMora-E2E-Long-Passphrase!');
  await page.getByRole('button', { name: /Create free account/ }).click();
  await expect(page).toHaveURL(/\/app\/dashboard/, { timeout: 30_000 });
  await expect(page.getByRole('heading', { name: /Welcome back/ })).toBeVisible();

  await page.goto('/app/markets');
  await expect(page.getByRole('heading', { name: 'Explore live currency markets.' })).toBeVisible();
  await expect(page.getByText(/TradingView provider data may differ by feed/)).toBeVisible();
  await expect(page.locator('.provider-market-main .provider-widget-advanced')).toBeVisible();

  await page.goto('/app/economic-calendar');
  await expect(page.getByRole('heading', { name: /Economic calendar/i })).toBeVisible();

  await page.goto('/app/demo-trading');
  const place = page.getByRole('button', { name: /Place simulated buy order/ });
  await expect(place).toBeEnabled({ timeout: 30_000 });
  await page.getByLabel('Reasoning / trade plan').fill('Synthetic EUR/USD trend exercise with explicit risk limits.');
  await page.getByLabel('Strategy tag').fill('E2E evidence check');
  await place.click();
  await expect(page.getByText('Simulated position opened and saved.')).toBeVisible();
  const close = page.getByRole('button', { name: 'Close trade' });
  await expect(close).toBeVisible();
  await close.click();
  await expect(page.getByText(/Automatically saved to the journal/)).toBeVisible();

  await page.goto('/app/trading-journal');
  await expect(page.getByRole('heading', { name: 'Trading journal.' })).toBeVisible();
  await expect(page.locator('.data-table tbody tr').first()).toContainText('EUR/USD');
  await expect(page.locator('.data-table tbody tr').first()).toContainText('DEMO');
  await page.getByRole('link', { name: /AI review/ }).first().click();
  await expect(page).toHaveURL(/\/app\/ai-coach\?trade=/);
  await page.getByRole('button', { name: /Generate evidence-based review/ }).click();
  await expect(page.getByText(/Based on 1 recorded trades/)).toBeVisible();

  await page.goto('/app/my-analytics');
  await expect(page.getByRole('heading', { name: 'Progress, in perspective.' })).toBeVisible();
  await expect(page.getByText('Only 1 recorded trades')).toBeVisible();
});