package com.example.tests;

import org.junit.jupiter.api.Test;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;

/**
 * Test class with intentional gTAA violations for demonstration.
 *
 * Violations:
 * - ADAPTATION_IN_DEFINITION: Direct browser calls in @Test methods
 * - HARDCODED_TEST_DATA: Email and URL strings
 * - POOR_TEST_NAMING: Test1, TestA methods
 */
public class LoginTest {

    private WebDriver driver;

    @Test
    public void test1() {
        // VIOLATION: POOR_TEST_NAMING - generic name
        // VIOLATION: ADAPTATION_IN_DEFINITION - direct findElement call
        driver = new ChromeDriver();
        driver.get("https://example.com/login");

        WebElement username = driver.findElement(By.id("username"));
        WebElement password = driver.findElement(By.id("password"));

        // VIOLATION: HARDCODED_TEST_DATA
        username.sendKeys("test@example.com");
        password.sendKeys("password123");

        driver.findElement(By.id("loginBtn")).click();
    }

    @Test
    public void testA() {
        // VIOLATION: POOR_TEST_NAMING
        // VIOLATION: ADAPTATION_IN_DEFINITION
        driver.findElement(By.cssSelector(".logout")).click();
    }

    @Test
    public void testUserCanLoginWithValidCredentials() {
        // Good name, but still has violations
        // VIOLATION: ADAPTATION_IN_DEFINITION
        driver.get("https://app.example.com/auth");
        driver.findElement(By.xpath("//input[@name='email']")).sendKeys("admin@company.org");
    }

    @Test
    public void testLongMethod() {
        // VIOLATION: LONG_TEST_FUNCTION (> 50 lines)
        driver.get("https://example.com");
        driver.findElement(By.id("field1")).sendKeys("value1");
        driver.findElement(By.id("field2")).sendKeys("value2");
        driver.findElement(By.id("field3")).sendKeys("value3");
        driver.findElement(By.id("field4")).sendKeys("value4");
        driver.findElement(By.id("field5")).sendKeys("value5");
        driver.findElement(By.id("field6")).sendKeys("value6");
        driver.findElement(By.id("field7")).sendKeys("value7");
        driver.findElement(By.id("field8")).sendKeys("value8");
        driver.findElement(By.id("field9")).sendKeys("value9");
        driver.findElement(By.id("field10")).sendKeys("value10");
        driver.findElement(By.id("field11")).sendKeys("value11");
        driver.findElement(By.id("field12")).sendKeys("value12");
        driver.findElement(By.id("field13")).sendKeys("value13");
        driver.findElement(By.id("field14")).sendKeys("value14");
        driver.findElement(By.id("field15")).sendKeys("value15");
        driver.findElement(By.id("field16")).sendKeys("value16");
        driver.findElement(By.id("field17")).sendKeys("value17");
        driver.findElement(By.id("field18")).sendKeys("value18");
        driver.findElement(By.id("field19")).sendKeys("value19");
        driver.findElement(By.id("field20")).sendKeys("value20");
        driver.findElement(By.id("field21")).sendKeys("value21");
        driver.findElement(By.id("field22")).sendKeys("value22");
        driver.findElement(By.id("field23")).sendKeys("value23");
        driver.findElement(By.id("field24")).sendKeys("value24");
        driver.findElement(By.id("field25")).sendKeys("value25");
        driver.findElement(By.id("field26")).sendKeys("value26");
        driver.findElement(By.id("field27")).sendKeys("value27");
        driver.findElement(By.id("field28")).sendKeys("value28");
        driver.findElement(By.id("field29")).sendKeys("value29");
        driver.findElement(By.id("field30")).sendKeys("value30");
        driver.findElement(By.id("field31")).sendKeys("value31");
        driver.findElement(By.id("field32")).sendKeys("value32");
        driver.findElement(By.id("field33")).sendKeys("value33");
        driver.findElement(By.id("field34")).sendKeys("value34");
        driver.findElement(By.id("field35")).sendKeys("value35");
        driver.findElement(By.id("submit")).click();
    }
}
