using OpenQA.Selenium;
using OpenQA.Selenium.Support.PageObjects;
// VIOLATION: FORBIDDEN_IMPORT - test framework import in Page Object
using NUnit.Framework;

namespace ExampleProject.Pages
{
    /// <summary>
    /// Page Object with intentional gTAA violations for demonstration.
    ///
    /// Violations:
    /// - FORBIDDEN_IMPORT: NUnit import in Page Object
    /// - ASSERTION_IN_POM: Assert calls inside Page Object methods
    /// </summary>
    public class LoginPage
    {
        private readonly IWebDriver _driver;

        [FindsBy(How = How.Id, Using = "username")]
        private IWebElement UsernameField { get; set; }

        [FindsBy(How = How.Id, Using = "password")]
        private IWebElement PasswordField { get; set; }

        [FindsBy(How = How.Id, Using = "loginBtn")]
        private IWebElement LoginButton { get; set; }

        [FindsBy(How = How.CssSelector, Using = ".error-message")]
        private IWebElement ErrorMessage { get; set; }

        public LoginPage(IWebDriver driver)
        {
            _driver = driver;
            PageFactory.InitElements(driver, this);
        }

        public void EnterUsername(string username)
        {
            UsernameField.Clear();
            UsernameField.SendKeys(username);
        }

        public void EnterPassword(string password)
        {
            PasswordField.Clear();
            PasswordField.SendKeys(password);
        }

        public void ClickLogin()
        {
            LoginButton.Click();
        }

        public void Login(string username, string password)
        {
            EnterUsername(username);
            EnterPassword(password);
            ClickLogin();
        }

        // VIOLATION: ASSERTION_IN_POM
        public void VerifyLoginSuccessful()
        {
            Assert.That(_driver.Url, Does.Contain("dashboard"));
        }

        // VIOLATION: ASSERTION_IN_POM
        public void VerifyErrorMessage(string expectedMessage)
        {
            Assert.AreEqual(expectedMessage, ErrorMessage.Text);
        }

        // VIOLATION: ASSERTION_IN_POM
        public void AssertUserIsLoggedIn()
        {
            Assert.IsNotNull(_driver.FindElement(By.Id("userAvatar")));
        }
    }
}
