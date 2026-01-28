"""
Test file with quality violations for Phase 3.

Violations present:
- POOR_TEST_NAMING: test_1, test_2 (generic names)
- HARDCODED_TEST_DATA: emails, URLs, phone numbers, passwords
- LONG_TEST_FUNCTION: test_very_long_checkout (>50 lines)
"""


def test_1():
    """Generic name — VIOLATION: POOR_TEST_NAMING."""
    email = "admin@example.com"          # VIOLATION: HARDCODED_TEST_DATA
    url = "https://shop.example.com/api"  # VIOLATION: HARDCODED_TEST_DATA
    phone = "555-123-4567"               # VIOLATION: HARDCODED_TEST_DATA
    assert email is not None


def test_2():
    """Generic name — VIOLATION: POOR_TEST_NAMING."""
    pwd = "MySecurePassword123"  # VIOLATION: HARDCODED_TEST_DATA
    assert pwd is not None


def test_very_long_checkout():
    """
    Long test — VIOLATION: LONG_TEST_FUNCTION (>50 lines).
    """
    step_01 = "Navigate to homepage"
    step_02 = "Click on products"
    step_03 = "Select category electronics"
    step_04 = "Click first product"
    step_05 = "Verify product title"
    step_06 = "Verify product price"
    step_07 = "Click add to cart"
    step_08 = "Verify cart count"
    step_09 = "Go to cart page"
    step_10 = "Verify item in cart"
    step_11 = "Click checkout"
    step_12 = "Enter first name"
    step_13 = "Enter last name"
    step_14 = "Enter street address"
    step_15 = "Enter city"
    step_16 = "Enter state"
    step_17 = "Enter zip code"
    step_18 = "Enter country"
    step_19 = "Enter phone number"
    step_20 = "Enter email"
    step_21 = "Select shipping method"
    step_22 = "Verify shipping cost"
    step_23 = "Enter card number"
    step_24 = "Enter expiry date"
    step_25 = "Enter CVV"
    step_26 = "Enter cardholder name"
    step_27 = "Click place order"
    step_28 = "Verify order confirmation"
    step_29 = "Verify order number"
    step_30 = "Verify order total"
    step_31 = "Verify email sent"
    step_32 = "Click continue shopping"
    step_33 = "Verify homepage loaded"
    step_34 = "Verify cart is empty"
    step_35 = "Check order history"
    step_36 = "Verify order in history"
    step_37 = "Verify order status"
    step_38 = "Verify delivery date"
    step_39 = "Click order details"
    step_40 = "Verify line items"
    step_41 = "Verify subtotal"
    step_42 = "Verify tax"
    step_43 = "Verify total matches"
    step_44 = "Click back to orders"
    step_45 = "Verify back on orders page"
    step_46 = "Log out"
    step_47 = "Verify logged out"
    step_48 = "Verify redirect to login"
    assert step_48 is not None
