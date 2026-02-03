# Feature con violaciones BDD intencionadas
# Expected violations:
# - GHERKIN_IMPLEMENTATION_DETAIL (líneas con XPath, URLs, CSS)
# - MISSING_THEN_STEP (Scenario sin Then)

Feature: Login functionality

  Scenario: User logs in with valid credentials
    Given I navigate to http://localhost:8080/login
    When I type "admin" into //input[@id='username']
    And I type "password123" into #password-field
    And I click on //button[@type='submit']
    Then I should see the dashboard

  Scenario: User logs in with invalid credentials
    Given I am on the login page
    When I enter invalid credentials
    And I click the submit button

  Scenario: Admin access check
    Given I open the page at http://localhost:8080/admin
    When I run SELECT * FROM users WHERE role='admin'
    Then the admin panel should be visible
