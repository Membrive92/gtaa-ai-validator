"""
Step definitions adicionales — contiene step pattern duplicado.

Expected violations:
- DUPLICATE_STEP_PATTERN (misma regex que login_steps.py)
- STEP_DEF_DIRECT_BROWSER_CALL
"""

from behave import given, when, then


@given("I am on the login page")
def step_on_login(context):
    # VIOLACIÓN: DUPLICATE_STEP_PATTERN (duplicado de login_steps.py)
    # VIOLACIÓN: STEP_DEF_DIRECT_BROWSER_CALL
    context.page.locator("#login-form").wait_for()


@when("I search for {query}")
def step_search(context, query):
    # VIOLACIÓN: STEP_DEF_DIRECT_BROWSER_CALL
    context.driver.find_element("id", "search-input").send_keys(query)
    context.driver.find_element("id", "search-btn").click()


@then("I should see results for {query}")
def step_verify_results(context, query):
    results = context.driver.find_element("id", "results")
    assert query in results.text
