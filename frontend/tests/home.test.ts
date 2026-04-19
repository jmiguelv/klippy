import { expect, test } from '@playwright/test';

test('home page has expected h1', async ({ page }) => {
	await page.goto('/');
	await expect(page.locator('h1')).toBeVisible();
	await expect(page.locator('h1')).toContainText('Ask anything about');
});

test('search form is present', async ({ page }) => {
	await page.goto('/');
	await expect(page.locator('input[type="text"]')).toBeVisible();
	await expect(page.locator('button[type="submit"]')).toBeVisible();
});
