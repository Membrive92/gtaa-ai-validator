using NUnit.Framework;
using OpenQA.Selenium;
using OpenQA.Selenium.Chrome;

namespace ExampleProject.Tests
{
    /// <summary>
    /// Test class with intentional gTAA violations for demonstration.
    ///
    /// Violations:
    /// - ADAPTATION_IN_DEFINITION: Direct FindElement calls in [Test] methods
    /// - HARDCODED_TEST_DATA: Email and URL strings
    /// - POOR_TEST_NAMING: Test1, TestA methods
    /// </summary>
    [TestFixture]
    public class LoginTests
    {
        private IWebDriver _driver;

        [SetUp]
        public void SetUp()
        {
            _driver = new ChromeDriver();
        }

        [TearDown]
        public void TearDown()
        {
            _driver?.Quit();
        }

        // VIOLATION: POOR_TEST_NAMING
        [Test]
        public void Test1()
        {
            // VIOLATION: ADAPTATION_IN_DEFINITION
            _driver.Navigate().GoToUrl("https://example.com/login");

            // VIOLATION: ADAPTATION_IN_DEFINITION
            var username = _driver.FindElement(By.Id("username"));
            var password = _driver.FindElement(By.Id("password"));

            // VIOLATION: HARDCODED_TEST_DATA
            username.SendKeys("test@example.com");
            password.SendKeys("password123");

            _driver.FindElement(By.Id("loginBtn")).Click();
        }

        // VIOLATION: POOR_TEST_NAMING
        [Test]
        public void TestA()
        {
            // VIOLATION: ADAPTATION_IN_DEFINITION
            _driver.FindElement(By.CssSelector(".logout")).Click();
        }

        [Test]
        public void TestUserCanLoginWithValidCredentials()
        {
            // Good name, but still has violations
            // VIOLATION: ADAPTATION_IN_DEFINITION
            _driver.Navigate().GoToUrl("https://app.example.com/auth");
            // VIOLATION: HARDCODED_TEST_DATA
            _driver.FindElement(By.XPath("//input[@name='email']")).SendKeys("admin@company.org");
        }

        [Test]
        public void TestLongMethod()
        {
            // VIOLATION: LONG_TEST_FUNCTION (> 50 lines)
            _driver.Navigate().GoToUrl("https://example.com");
            _driver.FindElement(By.Id("field1")).SendKeys("value1");
            _driver.FindElement(By.Id("field2")).SendKeys("value2");
            _driver.FindElement(By.Id("field3")).SendKeys("value3");
            _driver.FindElement(By.Id("field4")).SendKeys("value4");
            _driver.FindElement(By.Id("field5")).SendKeys("value5");
            _driver.FindElement(By.Id("field6")).SendKeys("value6");
            _driver.FindElement(By.Id("field7")).SendKeys("value7");
            _driver.FindElement(By.Id("field8")).SendKeys("value8");
            _driver.FindElement(By.Id("field9")).SendKeys("value9");
            _driver.FindElement(By.Id("field10")).SendKeys("value10");
            _driver.FindElement(By.Id("field11")).SendKeys("value11");
            _driver.FindElement(By.Id("field12")).SendKeys("value12");
            _driver.FindElement(By.Id("field13")).SendKeys("value13");
            _driver.FindElement(By.Id("field14")).SendKeys("value14");
            _driver.FindElement(By.Id("field15")).SendKeys("value15");
            _driver.FindElement(By.Id("field16")).SendKeys("value16");
            _driver.FindElement(By.Id("field17")).SendKeys("value17");
            _driver.FindElement(By.Id("field18")).SendKeys("value18");
            _driver.FindElement(By.Id("field19")).SendKeys("value19");
            _driver.FindElement(By.Id("field20")).SendKeys("value20");
            _driver.FindElement(By.Id("field21")).SendKeys("value21");
            _driver.FindElement(By.Id("field22")).SendKeys("value22");
            _driver.FindElement(By.Id("field23")).SendKeys("value23");
            _driver.FindElement(By.Id("field24")).SendKeys("value24");
            _driver.FindElement(By.Id("field25")).SendKeys("value25");
            _driver.FindElement(By.Id("field26")).SendKeys("value26");
            _driver.FindElement(By.Id("field27")).SendKeys("value27");
            _driver.FindElement(By.Id("field28")).SendKeys("value28");
            _driver.FindElement(By.Id("field29")).SendKeys("value29");
            _driver.FindElement(By.Id("field30")).SendKeys("value30");
            _driver.FindElement(By.Id("field31")).SendKeys("value31");
            _driver.FindElement(By.Id("field32")).SendKeys("value32");
            _driver.FindElement(By.Id("field33")).SendKeys("value33");
            _driver.FindElement(By.Id("field34")).SendKeys("value34");
            _driver.FindElement(By.Id("field35")).SendKeys("value35");
            _driver.FindElement(By.Id("submit")).Click();
        }
    }
}
