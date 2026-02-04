package com.example.pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.FindBy;
import org.openqa.selenium.support.PageFactory;
// VIOLATION: FORBIDDEN_IMPORT - test framework import in Page Object
import org.junit.jupiter.api.Assertions;

/**
 * Page Object with intentional gTAA violations for demonstration.
 *
 * Violations:
 * - FORBIDDEN_IMPORT: JUnit import in Page Object
 * - ASSERTION_IN_POM: Assertions inside Page Object methods
 */
public class LoginPage {

    private WebDriver driver;

    @FindBy(id = "username")
    private WebElement usernameField;

    @FindBy(id = "password")
    private WebElement passwordField;

    @FindBy(id = "loginBtn")
    private WebElement loginButton;

    @FindBy(css = ".error-message")
    private WebElement errorMessage;

    public LoginPage(WebDriver driver) {
        this.driver = driver;
        PageFactory.initElements(driver, this);
    }

    public void enterUsername(String username) {
        usernameField.clear();
        usernameField.sendKeys(username);
    }

    public void enterPassword(String password) {
        passwordField.clear();
        passwordField.sendKeys(password);
    }

    public void clickLogin() {
        loginButton.click();
    }

    public void login(String username, String password) {
        enterUsername(username);
        enterPassword(password);
        clickLogin();
    }

    // VIOLATION: ASSERTION_IN_POM
    public void verifyLoginSuccessful() {
        Assertions.assertTrue(driver.getCurrentUrl().contains("dashboard"));
    }

    // VIOLATION: ASSERTION_IN_POM
    public void verifyErrorMessage(String expectedMessage) {
        Assertions.assertEquals(expectedMessage, errorMessage.getText());
    }

    // VIOLATION: ASSERTION_IN_POM
    public void assertUserIsLoggedIn() {
        Assertions.assertNotNull(driver.findElement(By.id("userAvatar")));
    }
}
