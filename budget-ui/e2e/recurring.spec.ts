import { test, expect } from '@playwright/test';
import { freshEmail, registerAndLogin, addCategory, goToTab, TEST_PASSWORD } from './helpers';

/**
 * Covers the proposal's V2 commitment: "Recurring transactions like rent
 * and salary are automatically added each month on the set date" and its
 * system testing plan: "whether recurring transactions are added
 * automatically on the set date."
 */
test.describe('Recurring Transactions', () => {
  test('creating an income rule shows it in the table', async ({ page }) => {
    await registerAndLogin(page, freshEmail('rec-income'));
    await goToTab(page, 'recurring');

    await page.getByTestId('recurring-type-select').selectOption('income');
    await page.getByTestId('recurring-amount-input').fill('3000');
    await page.getByTestId('recurring-day-input').fill('1');
    await page.getByTestId('recurring-note-input').fill('Salary');
    await page.getByTestId('add-recurring-btn').click();

    await expect(page.getByTestId('recurring-table')).toContainText('income');
    await expect(page.getByTestId('recurring-table')).toContainText('3000');
    await expect(page.getByTestId('recurring-table')).toContainText('Salary');
  });

  test('an expense rule requires choosing a category', async ({ page }) => {
    await registerAndLogin(page, freshEmail('rec-expense-nocat'));
    await addCategory(page, 'Rent', 900);
    await goToTab(page, 'recurring');

    await page.getByTestId('recurring-type-select').selectOption('expense');
    await page.getByTestId('recurring-amount-input').fill('900');
    await page.getByTestId('recurring-day-input').fill('1');
    // Deliberately leave the category as "-- choose --" (null).
    await page.getByTestId('add-recurring-btn').click();

    await expect(page.getByTestId('recurring-error')).toBeVisible();
    await expect(page.getByTestId('recurring-table')).toHaveCount(0);
  });

  test('an expense rule with a category is created successfully', async ({ page }) => {
    await registerAndLogin(page, freshEmail('rec-expense-cat'));
    await addCategory(page, 'Rent', 900);
    await goToTab(page, 'recurring');

    await page.getByTestId('recurring-type-select').selectOption('expense');
    await page.getByTestId('recurring-amount-input').fill('900');
    await page.getByTestId('recurring-category-select').selectOption({ label: 'Rent' });
    await page.getByTestId('recurring-day-input').fill('1');
    await page.getByTestId('recurring-note-input').fill('Rent payment');
    await page.getByTestId('add-recurring-btn').click();

    await expect(page.getByTestId('recurring-table')).toContainText('expense');
    await expect(page.getByTestId('recurring-table')).toContainText('Rent payment');
  });

  test('rejects an invalid day of month', async ({ page }) => {
    await registerAndLogin(page, freshEmail('rec-badday'));
    await goToTab(page, 'recurring');

    await page.getByTestId('recurring-type-select').selectOption('income');
    await page.getByTestId('recurring-amount-input').fill('3000');
    await page.getByTestId('recurring-day-input').fill('31'); // backend only allows 1-28
    await page.getByTestId('add-recurring-btn').click();

    await expect(page.getByTestId('recurring-error')).toBeVisible();
    await expect(page.getByTestId('recurring-table')).toHaveCount(0);
  });

  test('deleting a rule removes it from the table', async ({ page }) => {
    await registerAndLogin(page, freshEmail('rec-delete'));
    await goToTab(page, 'recurring');

    await page.getByTestId('recurring-type-select').selectOption('income');
    await page.getByTestId('recurring-amount-input').fill('3000');
    await page.getByTestId('recurring-day-input').fill('1');
    await page.getByTestId('add-recurring-btn').click();
    await expect(page.getByTestId('recurring-table')).toBeVisible();

    await page.getByTestId('delete-recurring-btn').click();
    await expect(page.getByTestId('recurring-table')).toHaveCount(0);
  });

  test('a rule due on day 1 auto-generates a transaction the next time the user logs in', async ({ page }) => {
    // day_of_month = 1 is always "due" no matter what day the suite runs on,
    // since generate_due_transactions() fires for any day on/after the set day.
    const email = freshEmail('rec-fire');

    await registerAndLogin(page, email);
    await goToTab(page, 'recurring');
    await page.getByTestId('recurring-type-select').selectOption('income');
    await page.getByTestId('recurring-amount-input').fill('3000');
    await page.getByTestId('recurring-day-input').fill('1');
    await page.getByTestId('recurring-note-input').fill('Salary');
    await page.getByTestId('add-recurring-btn').click();
    await expect(page.getByTestId('recurring-table')).toContainText('Salary');

    // Log out and back in - both rollover and recurring generation run on login.
    await page.getByTestId('logout-btn').click();
    await expect(page).toHaveURL(/.*login/);
    await page.getByTestId('email-input').fill(email);
    await page.getByTestId('password-input').fill(TEST_PASSWORD);
    await page.getByTestId('submit-btn').click();
    await expect(page).toHaveURL(/.*dashboard/);

    await goToTab(page, 'transactions');
    await expect(page.getByTestId('transaction-table')).toContainText('Recurring');
    await expect(page.getByTestId('transaction-table')).toContainText('3000');
  });
});
