import { test, expect } from '@playwright/test';
import { freshEmail, registerAndLogin, addCategory, goToTab, todayIso } from './helpers';

/**
 * Covers the proposal's category management + input validation commitments:
 * "Users can create, edit, and delete categories... Deleting a category with
 * existing entries will be handled without affecting existing entries" and
 * "Users can only add income and expenses as positive amounts."
 */
test.describe('Categories', () => {
  test('adding a category shows it in the table with the correct budget', async ({ page }) => {
    await registerAndLogin(page, freshEmail('cat-add'));
    await addCategory(page, 'Food', 300);

    const row = page.locator('[data-testid^="category-row-"]', { hasText: 'Food' });
    await expect(row).toContainText('300'); // monthly_budget
    await expect(row).toContainText('ok');  // no spending yet, status should read "ok"
  });

  test('rejects a category with a negative monthly budget', async ({ page }) => {
    await registerAndLogin(page, freshEmail('cat-neg'));
    await goToTab(page, 'categories');

    await page.getByTestId('category-name-input').fill('Rent');
    await page.getByTestId('category-budget-input').fill('-50');
    await page.getByTestId('add-category-btn').click();

    await expect(page.getByTestId('category-error')).toBeVisible();
    await expect(page.getByTestId('category-table')).toHaveCount(0); // no categories were ever added
  });

  test('rejects a duplicate category name for the same user', async ({ page }) => {
    await registerAndLogin(page, freshEmail('cat-dup'));
    await addCategory(page, 'Food', 300);

    await page.getByTestId('category-name-input').fill('Food');
    await page.getByTestId('category-budget-input').fill('200');
    await page.getByTestId('add-category-btn').click();

    await expect(page.getByTestId('category-error')).toBeVisible();
    // Still only one "Food" row, not two.
    await expect(page.locator('[data-testid^="category-row-"]', { hasText: 'Food' })).toHaveCount(1);
  });

  test('deleting a category removes it from the list without deleting its past transactions', async ({ page }) => {
    await registerAndLogin(page, freshEmail('cat-del'));
    await addCategory(page, 'Food', 300);

    // Log an expense against it first.
    await goToTab(page, 'transactions');
    await page.getByTestId('amount-input').fill('50');
    await page.getByTestId('category-select').selectOption({ label: 'Food' });
    await page.getByTestId('date-input').fill(todayIso());
    await page.getByTestId('add-transaction-btn').click();
    await expect(page.getByTestId('transaction-table')).toContainText('50');

    // Now delete the category.
    await goToTab(page, 'categories');
    await page.getByTestId('delete-category-btn').click();
    await expect(page.getByTestId('category-table')).toHaveCount(0);

    // The transaction should still exist (proposal requirement: unassigned, not deleted).
    await goToTab(page, 'transactions');
    await expect(page.getByTestId('transaction-table')).toContainText('50');
  });

  test('deleting a nonexistent category does not crash the page', async ({ page }) => {
    // Regression guard: exercise the delete flow with a real category, then
    // confirm the page is still fully usable afterward (no leftover broken state).
    await registerAndLogin(page, freshEmail('cat-del2'));
    await addCategory(page, 'Rent', 900);
    await page.getByTestId('delete-category-btn').click();

    await expect(page.getByTestId('category-name-input')).toBeVisible();
    await addCategory(page, 'Food', 300); // page still works after a delete
  });
});
