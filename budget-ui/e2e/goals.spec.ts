import { test, expect } from '@playwright/test';
import { freshEmail, registerAndLogin, goToTab } from './helpers';

/**
 * Covers the proposal's V2 commitment: "Users can now set a saving goal...
 * Based on the average monthly contributions needed, it shows how close
 * the savings are and how much remains."
 */

/** A date far enough in the future that local/UTC timezone differences never matter. */
function futureDate(daysAhead = 60): string {
  const d = new Date();
  d.setDate(d.getDate() + daysAhead);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

test.describe('Savings Goals', () => {
  test('creating a goal shows it with 0% progress', async ({ page }) => {
    await registerAndLogin(page, freshEmail('goal-add'));
    await goToTab(page, 'goals');

    await page.getByTestId('goal-name-input').fill('Vacation Fund');
    await page.getByTestId('goal-amount-input').fill('5000');
    await page.getByTestId('goal-date-input').fill(futureDate());
    await page.getByTestId('add-goal-btn').click();

    const card = page.locator('[data-testid^="goal-card-"]', { hasText: 'Vacation Fund' });
    await expect(card).toContainText('0 / 5000');
    await expect(card).toContainText('0%');
  });

  test('rejects a target date that is not in the future', async ({ page }) => {
    await registerAndLogin(page, freshEmail('goal-pastdate'));
    await goToTab(page, 'goals');

    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');

    await page.getByTestId('goal-name-input').fill('Bad Goal');
    await page.getByTestId('goal-amount-input').fill('1000');
    await page.getByTestId('goal-date-input').fill(`${year}-${month}-${day}`); // today, not future
    await page.getByTestId('add-goal-btn').click();

    await expect(page.getByTestId('goal-error')).toBeVisible();
    await expect(page.locator('[data-testid^="goal-card-"]')).toHaveCount(0);
  });

  test('rejects a negative target amount', async ({ page }) => {
    await registerAndLogin(page, freshEmail('goal-negamount'));
    await goToTab(page, 'goals');

    await page.getByTestId('goal-name-input').fill('Bad Goal');
    await page.getByTestId('goal-amount-input').fill('-500');
    await page.getByTestId('goal-date-input').fill(futureDate());
    await page.getByTestId('add-goal-btn').click();

    await expect(page.getByTestId('goal-error')).toBeVisible();
    await expect(page.locator('[data-testid^="goal-card-"]')).toHaveCount(0);
  });

  test('adding a contribution updates the progress bar and percentage', async ({ page }) => {
    await registerAndLogin(page, freshEmail('goal-contribute'));
    await goToTab(page, 'goals');

    await page.getByTestId('goal-name-input').fill('New Laptop');
    await page.getByTestId('goal-amount-input').fill('1000');
    await page.getByTestId('goal-date-input').fill(futureDate());
    await page.getByTestId('add-goal-btn').click();

    const card = page.locator('[data-testid^="goal-card-"]', { hasText: 'New Laptop' });
    const contributeInput = card.locator('input[type="number"]');
    await contributeInput.fill('250');
    await card.getByRole('button', { name: 'Add contribution' }).click();

    await expect(card).toContainText('250 / 1000');
    await expect(card).toContainText('25%');
  });

  test('deleting a goal removes its card', async ({ page }) => {
    await registerAndLogin(page, freshEmail('goal-delete'));
    await goToTab(page, 'goals');

    await page.getByTestId('goal-name-input').fill('Emergency Fund');
    await page.getByTestId('goal-amount-input').fill('2000');
    await page.getByTestId('goal-date-input').fill(futureDate());
    await page.getByTestId('add-goal-btn').click();
    await expect(page.locator('[data-testid^="goal-card-"]')).toHaveCount(1);

    await page.getByTestId('delete-goal-btn').click();
    await expect(page.locator('[data-testid^="goal-card-"]')).toHaveCount(0);
  });
});
