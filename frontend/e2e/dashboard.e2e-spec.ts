import { test, expect, Page } from '@playwright/test';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const BASE_URL = 'http://localhost:4200';
const API_BASE = '/api/v1';
const AUTH_TOKEN_KEY = 'auth_token';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function seedTokenInLocalStorage(page: Page, token: string): Promise<void> {
  await page.addInitScript(
    ({ key, value }: { key: string; value: string }) => {
      localStorage.setItem(key, value);
    },
    { key: AUTH_TOKEN_KEY, value: token }
  );
}

async function mockGetProfile(page: Page, email: string): Promise<void> {
  await page.route(`**${API_BASE}/auth/me`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ email }),
    });
  });
}

async function mockChangePasswordSuccess(page: Page, newToken = 'e2e-new-token'): Promise<void> {
  await page.route(`**${API_BASE}/auth/change-password`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ access_token: newToken, token_type: 'bearer' }),
    });
  });
}

async function mockChangePasswordIncorrectCurrentPassword(page: Page): Promise<void> {
  await page.route(`**${API_BASE}/auth/change-password`, async (route) => {
    await route.fulfill({
      status: 401,
      contentType: 'application/json',
      body: JSON.stringify({ detail: 'Current password is incorrect.' }),
    });
  });
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

test.describe('Dashboard — unauthenticated access', () => {
  test('navigating to /dashboard without a token redirects to /login', async ({ page }) => {
    // No token is seeded — localStorage is empty
    await page.goto(`${BASE_URL}/dashboard`);

    await expect(page).toHaveURL(/\/login/);
  });
});

test.describe('Dashboard — authenticated user profile display', () => {
  test('email field is populated, read-only, and cannot be edited', async ({ page }) => {
    const token = 'e2e-dashboard-profile-token';
    const userEmail = 'user@example.com';

    await seedTokenInLocalStorage(page, token);
    await mockGetProfile(page, userEmail);

    await page.goto(`${BASE_URL}/dashboard`);

    await expect(page).toHaveURL(/\/dashboard/);

    // Email input must be visible and populated
    const emailInput = page.getByTestId('email-input');
    await expect(emailInput).toBeVisible();
    await expect(emailInput).toHaveValue(userEmail);

    // The input must have the disabled attribute (read-only, cannot be edited)
    await expect(emailInput).toBeDisabled();

    // Attempt to type into the disabled input should have no effect
    await emailInput.fill('hacker@evil.com').catch(() => {
      // fill() may throw on a disabled element — that is the desired behaviour
    });
    await expect(emailInput).toHaveValue(userEmail);
  });
});

test.describe('Dashboard — change-password form validation', () => {
  test('submitting with all fields empty shows per-field required error messages', async ({
    page,
  }) => {
    const token = 'e2e-dashboard-validation-token';

    await seedTokenInLocalStorage(page, token);
    await mockGetProfile(page, 'user@example.com');

    await page.goto(`${BASE_URL}/dashboard`);
    await expect(page).toHaveURL(/\/dashboard/);

    // Touch each field without entering any value so that required errors are triggered
    await page.getByTestId('current-password-input').click();
    await page.getByTestId('new-password-input').click();
    await page.getByTestId('confirm-password-input').click();

    // Click somewhere else to blur the last field
    await page.getByRole('heading', { name: /my account/i }).click();

    // All three required-error messages should be visible
    await expect(page.getByTestId('current-password-required-error')).toBeVisible();
    await expect(page.getByTestId('new-password-required-error')).toBeVisible();
    await expect(page.getByTestId('confirm-password-required-error')).toBeVisible();
  });

  test('submitting with mismatched new and confirm passwords shows mismatch error and makes no HTTP request', async ({
    page,
  }) => {
    const token = 'e2e-dashboard-mismatch-token';
    let changePasswordCalled = false;

    await seedTokenInLocalStorage(page, token);
    await mockGetProfile(page, 'user@example.com');

    // Intercept the change-password endpoint to detect if it is ever called
    await page.route(`**${API_BASE}/auth/change-password`, async (route) => {
      changePasswordCalled = true;
      await route.continue();
    });

    await page.goto(`${BASE_URL}/dashboard`);
    await expect(page).toHaveURL(/\/dashboard/);

    await page.getByTestId('current-password-input').fill('currentPass1');
    await page.getByTestId('new-password-input').fill('newpassword1');
    await page.getByTestId('confirm-password-input').fill('differentpassword1');

    // Confirm field must be touched to reveal the mismatch error
    await page.getByTestId('confirm-password-input').blur();

    // Mismatch error must be visible
    await expect(page.getByTestId('passwords-mismatch-error')).toBeVisible();

    // Submit button must remain disabled because the form is invalid
    const submitBtn = page.getByRole('button', { name: /change password/i });
    await expect(submitBtn).toBeDisabled();

    // No HTTP request must have been made
    expect(changePasswordCalled).toBe(false);
  });
});

test.describe('Dashboard — change-password form submission', () => {
  test('successful password change shows success message and clears all password fields', async ({
    page,
  }) => {
    const token = 'e2e-dashboard-success-token';

    await seedTokenInLocalStorage(page, token);
    await mockGetProfile(page, 'user@example.com');
    await mockChangePasswordSuccess(page, 'e2e-new-access-token');

    await page.goto(`${BASE_URL}/dashboard`);
    await expect(page).toHaveURL(/\/dashboard/);

    await page.getByTestId('current-password-input').fill('correctPass1');
    await page.getByTestId('new-password-input').fill('newValidPass1');
    await page.getByTestId('confirm-password-input').fill('newValidPass1');

    await page.getByRole('button', { name: /change password/i }).click();

    // Success message must appear
    await expect(page.getByTestId('success-message')).toBeVisible();

    // All three password fields must be cleared after a successful submission
    await expect(page.getByTestId('current-password-input')).toHaveValue('');
    await expect(page.getByTestId('new-password-input')).toHaveValue('');
    await expect(page.getByTestId('confirm-password-input')).toHaveValue('');
  });

  test('submitting with an incorrect current password shows server error on that field and retains values', async ({
    page,
  }) => {
    const token = 'e2e-dashboard-incorrect-token';

    await seedTokenInLocalStorage(page, token);
    await mockGetProfile(page, 'user@example.com');
    await mockChangePasswordIncorrectCurrentPassword(page);

    await page.goto(`${BASE_URL}/dashboard`);
    await expect(page).toHaveURL(/\/dashboard/);

    await page.getByTestId('current-password-input').fill('wrongCurrentPass');
    await page.getByTestId('new-password-input').fill('newValidPass1');
    await page.getByTestId('confirm-password-input').fill('newValidPass1');

    await page.getByRole('button', { name: /change password/i }).click();

    // Incorrect-current-password error must be visible
    await expect(page.getByTestId('current-password-incorrect-error')).toBeVisible();

    // New password and confirm fields must retain their values
    await expect(page.getByTestId('new-password-input')).toHaveValue('newValidPass1');
    await expect(page.getByTestId('confirm-password-input')).toHaveValue('newValidPass1');
  });
});
