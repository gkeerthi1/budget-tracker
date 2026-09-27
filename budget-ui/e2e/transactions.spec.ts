import { test, expect } from '@playwright/test';
import { freshEmail, registerAndLogin, addCategory, todayIso, goToTab } from './helpers';

/**
 * Covers the proposal's V1 commitments:
 * "adding income and expenses... crossing the 80% threshold, and invalid
 * inputs like negative amounts and future dates."
 */
test.describe('Transactions', () => {
  test('adding an income transaction with no category shows in the table', async ({ page }) => {
    await registerAndLogin(page, freshEmail('txn-income'));
    await goToTab(page, 'transactions');

    await page.getByTestId('type-select').selectOption('income');
    await page.getByTestId('amount-input').fill('2000');
    await page.getByTestId('date-input').fill(todayIso());
    await page.getByTestId('note-input').fill('Paycheck');
    await page.getByTestId('add-transaction-btn').click();

    await expect(page.getByTestId('transaction-table')).toContainText('2000');
    await expect(page.getByTestId('transaction-table')).toContainText('Paycheck');
  });

  test('rejects a negative expense amount', async ({ page }) => {
    await registerAndLogin(page, freshEmail('txn-neg'));
    await addCategory(page, 'Food', 300);
    await goToTab(page, 'transactions');

    await page.getByTestId('amount-input').fill('-50');
    await page.getByTestId('category-select').selectOption({ label: 'Food' });
    await page.getByTestId('date-input').fill(todayIso());
    await page.getByTestId('add-transaction-btn').click();

    await expect(page.getByTestId('transaction-error')).toBeVisible();
    await expect(page.getByTestId('transaction-table')).toHaveCount(0);
  });

  test('rejects a transaction dated in the future', async ({ page }) => {
    await registerAndLogin(page, freshEmail('txn-future'));
    await addCategory(page, 'Food', 300);
    await goToTab(page, 'transactions');

    const future = new Date();
    future.setFullYear(future.getFullYear() + 1);
    const futureIso = future.toISOString().slice(0, 10);

    await page.getByTestId('amount-input').fill('50');
    await page.getByTestId('category-select').selectOption({ label: 'Food' });
    await page.getByTestId('date-input').fill(futureIso);
    await page.getByTestId('add-transaction-btn').click();

    await expect(page.getByTestId('transaction-error')).toBeVisible();
    await expect(page.getByTestId('transaction-table')).toHaveCount(0);
  });

  test('shows an "approaching limit" warning at 80% of the category budget', async ({ page }) => {
    await registerAndLogin(page, freshEmail('txn-80'));
    await addCategory(page, 'Food', 100);
    await goToTab(page, 'transactions');

    await page.getByTestId('amount-input').fill('80');
    await page.getByTestId('category-select').selectOption({ label: 'Food' });
    await page.getByTestId('date-input').fill(todayIso());
    await page.getByTestId('add-transaction-btn').click();

    await expect(page.getByTestId('budget-warning')).toContainText('Approaching');
  });

  test('shows an "over budget" warning once spending exceeds the category budget', async ({ page }) => {
    await registerAndLogin(page, freshEmail('txn-over'));
    await addCategory(page, 'Food', 100);
    await goToTab(page, 'transactions');

    await page.getByTestId('amount-input').fill('150');
    await page.getByTestId('category-select').selectOption({ label: 'Food' });
    await page.getByTestId('date-input').fill(todayIso());
    await page.getByTestId('add-transaction-btn').click();

    await expect(page.getByTestId('budget-warning')).toContainText('Over budget');
  });

  test('shows no warning for spending well under the threshold', async ({ page }) => {
    await registerAndLogin(page, freshEmail('txn-under'));
    await addCategory(page, 'Food', 300);
    await goToTab(page, 'transactions');

    await page.getByTestId('amount-input').fill('50');
    await page.getByTestId('category-select').selectOption({ label: 'Food' });
    await page.getByTestId('date-input').fill(todayIso());
    await page.getByTestId('add-transaction-btn').click();

    await expect(page.getByTestId('budget-warning')).toHaveCount(0);
  });

  test('an expense requires choosing a category', async ({ page }) => {
    await registerAndLogin(page, freshEmail('txn-nocat'));
    await addCategory(page, 'Food', 300);
    await goToTab(page, 'transactions');

    // Leave category as "-- choose --" (null) and submit an expense.
    await page.getByTestId('amount-input').fill('50');
    await page.getByTestId('date-input').fill(todayIso());
    await page.getByTestId('add-transaction-btn').click();

    await expect(page.getByTestId('transaction-error')).toBeVisible();
  });
});
