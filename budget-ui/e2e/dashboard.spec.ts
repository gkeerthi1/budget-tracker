import { test, expect } from '@playwright/test';
import { freshEmail, registerAndLogin, addCategory, goToTab, todayIso } from './helpers';

/**
 * Covers the proposal's V1 dashboard commitment ("total income, total
 * expenses, and remaining balance per category") and the V2 extension
 * ("month-to-month comparison... trends in each category").
 */
test.describe('Dashboard', () => {
  test('shows correct income, expense, and net totals', async ({ page }) => {
    await registerAndLogin(page, freshEmail('dash-totals'));
    await addCategory(page, 'Food', 300);

    await goToTab(page, 'transactions');
    await page.getByTestId('type-select').selectOption('income');
    await page.getByTestId('amount-input').fill('2000');
    await page.getByTestId('date-input').fill(todayIso());
    await page.getByTestId('add-transaction-btn').click();
    await expect(page.getByTestId('transaction-table')).toContainText('2000');

    await page.getByTestId('type-select').selectOption('expense');
    await page.getByTestId('amount-input').fill('150');
    await page.getByTestId('category-select').selectOption({ label: 'Food' });
    await page.getByTestId('date-input').fill(todayIso());
    await page.getByTestId('add-transaction-btn').click();
    await expect(page.getByTestId('transaction-table')).toContainText('150');

    await goToTab(page, 'dashboard');
    await expect(page.getByTestId('total-income')).toHaveText('2000');
    await expect(page.getByTestId('total-expenses')).toHaveText('150');
    await expect(page.getByTestId('net-total')).toHaveText('1850');
  });

  test('reflects a category\'s effective budget, remaining balance, and status', async ({ page }) => {
    await registerAndLogin(page, freshEmail('dash-cat'));
    await addCategory(page, 'Food', 300);

    // 250/300 = ~83%, crosses the 80% "approaching_limit" threshold.
    await goToTab(page, 'transactions');
    await page.getByTestId('amount-input').fill('250');
    await page.getByTestId('category-select').selectOption({ label: 'Food' });
    await page.getByTestId('date-input').fill(todayIso());
    await page.getByTestId('add-transaction-btn').click();

    await goToTab(page, 'dashboard');
    const row = page.locator('[data-testid^="dashboard-row-"]', { hasText: 'Food' });
    await expect(row).toContainText('300'); // effective_budget
    await expect(row).toContainText('250'); // spent_this_month
    await expect(row).toContainText('50');  // remaining_balance
    await expect(row).toContainText('approaching_limit');
  });

  test('month-to-month comparison defaults to 6 months and includes the current month', async ({ page }) => {
    await registerAndLogin(page, freshEmail('dash-compare'));

    await goToTab(page, 'dashboard');
    await expect(page.getByTestId('compare-table')).toBeVisible();

    const rows = page.locator('[data-testid^="compare-row-"]');
    await expect(rows).toHaveCount(6);

    const currentMonth = todayIso().slice(0, 7); // yyyy-MM
    await expect(page.getByTestId(`compare-row-${currentMonth}`)).toBeVisible();
  });

  test('changing the months dropdown reloads the comparison with a different count', async ({ page }) => {
    await registerAndLogin(page, freshEmail('dash-months'));
    await goToTab(page, 'dashboard');

    await page.getByTestId('months-select').selectOption('3');
    await expect(page.locator('[data-testid^="compare-row-"]')).toHaveCount(3);

    await page.getByTestId('months-select').selectOption('12');
    await expect(page.locator('[data-testid^="compare-row-"]')).toHaveCount(12);
  });

  test('current month in the comparison reflects real spending entered this session', async ({ page }) => {
    await registerAndLogin(page, freshEmail('dash-compare-data'));
    await addCategory(page, 'Food', 300);

    await goToTab(page, 'transactions');
    await page.getByTestId('type-select').selectOption('income');
    await page.getByTestId('amount-input').fill('1000');
    await page.getByTestId('date-input').fill(todayIso());
    await page.getByTestId('add-transaction-btn').click();

    await goToTab(page, 'dashboard');
    const currentMonth = todayIso().slice(0, 7);
    const row = page.getByTestId(`compare-row-${currentMonth}`);
    await expect(row).toContainText('1000');
  });
});
