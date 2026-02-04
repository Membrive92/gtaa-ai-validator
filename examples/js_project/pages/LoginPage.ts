/**
 * Page Object with intentional gTAA violations for demonstration.
 *
 * Violations:
 * - ASSERTION_IN_POM: expect() calls inside Page Object methods
 */

import { Page, Locator, expect } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  readonly usernameInput: Locator;
  readonly passwordInput: Locator;
  readonly loginButton: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.usernameInput = page.locator('#username');
    this.passwordInput = page.locator('#password');
    this.loginButton = page.getByRole('button', { name: 'Login' });
    this.errorMessage = page.locator('.error-message');
  }

  async enterUsername(username: string) {
    await this.usernameInput.fill(username);
  }

  async enterPassword(password: string) {
    await this.passwordInput.fill(password);
  }

  async clickLogin() {
    await this.loginButton.click();
  }

  async login(username: string, password: string) {
    await this.enterUsername(username);
    await this.enterPassword(password);
    await this.clickLogin();
  }

  // VIOLATION: ASSERTION_IN_POM
  async verifyLoginSuccessful() {
    await expect(this.page).toHaveURL(/dashboard/);
  }

  // VIOLATION: ASSERTION_IN_POM
  async verifyErrorMessage(expectedMessage: string) {
    await expect(this.errorMessage).toHaveText(expectedMessage);
  }

  // VIOLATION: ASSERTION_IN_POM
  async assertUserIsLoggedIn() {
    await expect(this.page.locator('#userAvatar')).toBeVisible();
  }
}
