"""
Step definitions con violaciones BDD intencionadas.

Expected violations:
- STEP_DEF_DIRECT_BROWSER_CALL (llamadas directas a driver/page)
- STEP_DEF_TOO_COMPLEX (función > 15 líneas)
"""

from behave import given, when, then


@given("I am on the login page")
def step_navigate_login(context):
    # VIOLACIÓN: STEP_DEF_DIRECT_BROWSER_CALL
    # Debería usar un Page Object
    context.driver.find_element("id", "username")
    context.driver.find_element("id", "password")


@when("I enter valid credentials")
def step_enter_credentials(context):
    # VIOLACIÓN: STEP_DEF_DIRECT_BROWSER_CALL
    context.driver.find_element("id", "username").send_keys("admin")
    context.driver.find_element("id", "password").send_keys("secret")


@when("I click the submit button")
def step_click_submit(context):
    # VIOLACIÓN: STEP_DEF_DIRECT_BROWSER_CALL
    context.driver.find_element("css selector", "button[type=submit]").click()


@then("I should see the dashboard")
def step_verify_dashboard(context):
    # VIOLACIÓN: STEP_DEF_TOO_COMPLEX (> 15 líneas)
    # Esta función es intencionadamente larga
    dashboard = context.driver.find_element("id", "dashboard")
    assert dashboard is not None
    title = context.driver.find_element("class name", "title")
    assert title.text == "Dashboard"
    welcome = context.driver.find_element("id", "welcome-msg")
    assert "Welcome" in welcome.text
    sidebar = context.driver.find_element("id", "sidebar")
    assert sidebar.is_displayed()
    nav_items = context.driver.find_elements("class name", "nav-item")
    assert len(nav_items) > 0
    profile = context.driver.find_element("id", "profile-link")
    assert profile.is_displayed()
    logout = context.driver.find_element("id", "logout-btn")
    assert logout.is_displayed()
    footer = context.driver.find_element("tag name", "footer")
    assert footer is not None
"""
