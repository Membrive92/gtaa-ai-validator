/**
 * Test file with intentional gTAA violations for demonstration.
 *
 * Violations:
 * - ADAPTATION_IN_DEFINITION: Direct page.locator() calls in test()
 * - HARDCODED_TEST_DATA: Email strings
 * - POOR_TEST_NAMING: Generic test names
 */

import { test, expect } from '@playwright/test';

// VIOLATION: POOR_TEST_NAMING - generic describe name
describe('test', () => {

  // VIOLATION: POOR_TEST_NAMING - generic test name
  test('test 1', async ({ page }) => {
    // VIOLATION: ADAPTATION_IN_DEFINITION - direct locator calls
    await page.goto('https://example.com/login');
    await page.locator('#username').fill('user@example.com');  // VIOLATION: HARDCODED_TEST_DATA
    await page.locator('#password').fill('secret123');
    await page.getByRole('button', { name: 'Login' }).click();
  });

  // VIOLATION: POOR_TEST_NAMING
  test('test 2', async ({ page }) => {
    // VIOLATION: ADAPTATION_IN_DEFINITION
    await page.locator('.logout-button').click();
  });

  test('user can login with valid credentials', async ({ page }) => {
    // Good name, but still has violations
    // VIOLATION: ADAPTATION_IN_DEFINITION
    await page.goto('https://app.company.com/auth');
    // VIOLATION: HARDCODED_TEST_DATA
    await page.getByTestId('email-input').fill('admin@company.org');
    await page.getByTestId('password-input').fill('AdminPass!');
  });

  test('very long test function with too many steps', async ({ page }) => {
    // VIOLATION: LONG_TEST_FUNCTION (> 50 lines)
    await page.goto('https://example.com/form');
    await page.locator('#field1').fill('value1');
    await page.locator('#field2').fill('value2');
    await page.locator('#field3').fill('value3');
    await page.locator('#field4').fill('value4');
    await page.locator('#field5').fill('value5');
    await page.locator('#field6').fill('value6');
    await page.locator('#field7').fill('value7');
    await page.locator('#field8').fill('value8');
    await page.locator('#field9').fill('value9');
    await page.locator('#field10').fill('value10');
    await page.locator('#field11').fill('value11');
    await page.locator('#field12').fill('value12');
    await page.locator('#field13').fill('value13');
    await page.locator('#field14').fill('value14');
    await page.locator('#field15').fill('value15');
    await page.locator('#field16').fill('value16');
    await page.locator('#field17').fill('value17');
    await page.locator('#field18').fill('value18');
    await page.locator('#field19').fill('value19');
    await page.locator('#field20').fill('value20');
    await page.locator('#field21').fill('value21');
    await page.locator('#field22').fill('value22');
    await page.locator('#field23').fill('value23');
    await page.locator('#field24').fill('value24');
    await page.locator('#field25').fill('value25');
    await page.locator('#field26').fill('value26');
    await page.locator('#field27').fill('value27');
    await page.locator('#field28').fill('value28');
    await page.locator('#field29').fill('value29');
    await page.locator('#field30').fill('value30');
    await page.locator('#field31').fill('value31');
    await page.locator('#field32').fill('value32');
    await page.locator('#field33').fill('value33');
    await page.locator('#field34').fill('value34');
    await page.locator('#submit').click();
  });
});
