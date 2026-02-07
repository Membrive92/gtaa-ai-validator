# 🔍 CATÁLOGO DE ERRORES Y MALAS PRÁCTICAS PLANTADOS
# ====================================================
# Este archivo documenta TODOS los errores de arquitectura POM y malas prácticas
# intencionalmente sembrados en el proyecto, para validar tu escáner.
#
# Total: 60+ issues en 7 categorías

# ════════════════════════════════════════════════════
# 1. VIOLACIONES DEL PATRÓN PAGE OBJECT MODEL (POM)
# ════════════════════════════════════════════════════

## 1.1 Assertions dentro de Page Objects (deben estar SOLO en tests)
- pages/login_page.py → login() → `assert "dashboard" in self.page.url`
- pages/login_page.py → login() → `raise Exception(f"Login failed: {error_text}")` tras verificar
- pages/products_page.py → add_first_product_to_cart_and_verify() → `assert "added to cart" in toast_text`
- pages/products_page.py → add_first_product_to_cart_and_verify() → `assert int(cart_count) > 0`
- pages/product_detail_page.py → add_to_cart_and_verify() → `assert self.page.is_visible(self.SUCCESS_TOAST)`
- pages/cart_page.py → apply_promo_and_verify_discount() → `assert new_total == expected_total`
- pages/checkout_page.py → complete_checkout() → `assert self.page.is_visible(self.ORDER_CONFIRMATION)`
- pages/checkout_page.py → _verify_order_in_backend() → `assert resp.status_code == 200`
- pages/dashboard_page.py → change_password_flow() → `assert self.page.is_visible(".toast-success")`
- pages/dashboard_page.py → download_order_invoice() → `assert os.path.exists(invoice_file)`
- api/client.py → create_user() → `assert response.status_code == 201`
- api/client.py → create_product() → `assert response.status_code in [200, 201]`
- api/client.py → verify_product_lifecycle() → múltiples asserts

## 1.2 Lógica de negocio dentro de Page Objects
- pages/base_page.py → login() → Método de login en BasePage (no pertenece ahí)
- pages/base_page.py → get_user_from_db() → Acceso a BD en page object
- pages/base_page.py → get_product_via_api() → Llamada API en page object
- pages/products_page.py → calculate_cart_total() → Cálculos de carrito con tax rate hardcodeado
- pages/products_page.py → export_products_to_json() → Escritura de archivos desde page object
- pages/product_detail_page.py → complete_quick_purchase() → Flujo completo de compra
- pages/cart_page.py → complete_checkout_from_cart() → Checkout entero desde page object de Cart
- pages/dashboard_page.py → get_order_history_summary() → Transformación de datos/business logic
- pages/dashboard_page.py → download_order_invoice() → Operaciones de filesystem
- pages/login_page.py → generate_test_user() → Generación de datos de prueba en page object
- pages/login_page.py → bypass_captcha() → Manipulación directa de DOM

## 1.3 Page Objects que cruzan fronteras de página (violación SRP)
- pages/login_page.py → login_and_go_to_products() → Navega a Products y retorna ProductsPage
- pages/products_page.py → go_to_product_detail() → Retorna ProductDetailPage
- pages/product_detail_page.py → buy_now() → Retorna CheckoutPage
- pages/product_detail_page.py → complete_quick_purchase() → Interactúa con campos de checkout
- pages/cart_page.py → proceed_to_checkout() → Retorna CheckoutPage
- pages/cart_page.py → complete_checkout_from_cart() → Llena formularios de checkout y payment
- pages/checkout_page.py → back_to_cart() → Retorna CartPage
- pages/checkout_page.py → _verify_order_in_backend() → Llamada API desde page object

## 1.4 God Object / Clase con demasiadas responsabilidades
- pages/dashboard_page.py → Maneja: profile, orders, addresses, settings, wishlist, API, filesystem

## 1.5 Locators duplicados entre Page Objects
- SUCCESS_TOAST duplicado en: ProductsPage, ProductDetailPage
- CART_BADGE duplicado en: ProductsPage, CartPage

# ════════════════════════════════════════════════════
# 2. HARDCODED WAITS (time.sleep)
# ════════════════════════════════════════════════════

## Debe usar waits explícitos de Playwright (wait_for_selector, expect, etc.)
- pages/base_page.py → navigate() → time.sleep(3)
- pages/base_page.py → login() → time.sleep(2)
- pages/base_page.py → scroll_to_bottom() → time.sleep(1)
- pages/login_page.py → goto() → time.sleep(2)
- pages/login_page.py → login() → time.sleep(3)
- pages/login_page.py → social_login_google() → time.sleep(5)
- pages/products_page.py → _wait_for_products_load() → time.sleep(2) + time.sleep(1)
- pages/products_page.py → search_product() → time.sleep(3)
- pages/products_page.py → filter_by_category() → time.sleep(2)
- pages/products_page.py → sort_by() → time.sleep(2)
- pages/products_page.py → add_first_product_to_cart_and_verify() → time.sleep(2)
- pages/product_detail_page.py → add_to_cart() → time.sleep(2)
- pages/product_detail_page.py → buy_now() → time.sleep(2)
- pages/product_detail_page.py → complete_quick_purchase() → time.sleep(3) + time.sleep(5)
- pages/cart_page.py → goto() → time.sleep(2)
- pages/cart_page.py → remove_item() → time.sleep(2)
- pages/cart_page.py → complete_checkout_from_cart() → time.sleep(3) + time.sleep(5)
- pages/checkout_page.py → goto() → time.sleep(2)
- pages/checkout_page.py → place_order() → time.sleep(5)
- pages/dashboard_page.py → goto() → time.sleep(3)
- Y 15+ instancias más en tests/

# ════════════════════════════════════════════════════
# 3. CREDENCIALES Y DATOS SENSIBLES HARDCODEADOS
# ════════════════════════════════════════════════════

- config/settings.py → ADMIN_USERNAME = "admin@testapp.io"
- config/settings.py → ADMIN_PASSWORD = "Admin123!@#"
- config/settings.py → DB_HOST, DB_USER, DB_PASSWORD hardcodeados
- config/settings.py → API_KEY = "sk-live-abc123..."
- pages/login_page.py → DEFAULT_EMAIL, DEFAULT_PASSWORD, ADMIN_EMAIL, ADMIN_PASSWORD
- pages/cart_page.py → VALID_PROMO, EXPIRED_PROMO hardcodeados
- pages/checkout_page.py → fill_payment_info() → defaults con tarjeta de crédito
- pages/cart_page.py → complete_checkout_from_cart() → "4111111111111111" hardcodeado
- utils/helpers.py → TEST_USERS lista con credenciales
- utils/helpers.py → generate_credit_card() → generación de datos de tarjeta
- tests/test_login.py → VALID_EMAIL, VALID_PASSWORD, ADMIN_EMAIL, ADMIN_PASSWORD
- tests/test_checkout_e2e.py → SHIPPING_DATA hardcodeado en la clase

# ════════════════════════════════════════════════════
# 4. PROBLEMAS DE ARQUITECTURA DE TESTS
# ════════════════════════════════════════════════════

## 4.1 Tests que mezclan UI + API
- tests/test_login.py → test_login_creates_session_in_backend() → import requests dentro del test
- tests/test_products.py → test_new_product_appears_in_ui() → Crea producto via API, verifica en UI
- tests/test_checkout_e2e.py → test_complete_checkout_flow() → Verificación API al final
- tests/test_dashboard.py → test_orders_match_api() → Usa método API del dashboard page object

## 4.2 Tests demasiado largos / no atómicos
- tests/test_checkout_e2e.py → test_complete_checkout_flow() → 12 pasos en un solo test
- tests/test_login.py → test_login_and_navigate_to_products() → Cruza 2 funcionalidades

## 4.3 Dependencia entre tests
- tests/test_dashboard.py → test_change_password() → Cambia password sin cleanup (rompe tests posteriores)
- tests/test_cart.py → test_empty_cart_display() → Asume carrito vacío sin garantizarlo

## 4.4 Assertions débiles o sin sentido
- tests/test_dashboard.py → test_toggle_notifications() → `assert True`
- tests/test_dashboard.py → test_order_history() → `assert count >= 0` (nunca falla)
- tests/test_dashboard.py → test_wishlist() → `assert count >= 0` (nunca falla)
- tests/test_login.py → test_login_validation() → `assert expected_error in error or error != ""` (demasiado permisivo)

## 4.5 Login repetido por UI en cada test
- tests/test_products.py → test_products_page_loads() → login_page.login() en vez de usar fixture
- tests/test_cart.py → autouse fixture que hace login UI en cada test
- tests/test_dashboard.py → autouse fixture que hace login UI en cada test

## 4.6 Creación inline de Page Objects en tests (en vez de fixtures)
- tests/test_checkout_e2e.py → Múltiples `ProductsPage(page)`, `CartPage(page)` inline

# ════════════════════════════════════════════════════
# 5. PROBLEMAS DEL API CLIENT
# ════════════════════════════════════════════════════

- api/client.py → Almacena last_response/last_status_code como estado mutable
- api/client.py → create_user() genera datos de prueba (Faker) internamente
- api/client.py → generate_test_product() → generación de datos en el cliente
- api/client.py → verify_product_lifecycle() → test completo CRUD dentro del client
- api/client.py → save_response_to_file() → I/O de archivos en el client
- api/client.py → login_user() muta headers del session (estado compartido)
- api/client.py → _make_request() logea response.text (puede contener datos sensibles)
- api/client.py → Assertions dentro de métodos del client

# ════════════════════════════════════════════════════
# 6. SELECTORES FRÁGILES
# ════════════════════════════════════════════════════

- pages/login_page.py → FACEBOOK_LOGIN_BTN = "div.social-login > button:nth-child(2)" (posicional)
- pages/products_page.py → FIRST_PRODUCT = "div.product-grid > div:nth-child(1)" (posicional)
- pages/products_page.py → SECOND_PRODUCT/THIRD_PRODUCT (posicionales)
- pages/login_page.py → Mezcla de CSS, XPath, y text= selectores sin consistencia
- pages/products_page.py → Parseo frágil de precios con replace("$","")

# ════════════════════════════════════════════════════
# 7. MALAS PRÁCTICAS GENERALES
# ════════════════════════════════════════════════════

- pages/base_page.py → accept_cookies() → `except Exception: pass` (excepción silenciosa)
- pages/base_page.py → get_user_from_db() → SQL injection: f"SELECT * FROM users WHERE id = '{user_id}'"
- config/settings.py → ProductionConfig → Tests configurados para producción
- conftest.py → Variables globales `_browser_instance`, `_api_client_instance`
- conftest.py → Browser args: --disable-web-security, --no-sandbox
- conftest.py → ignore_https_errors=True
- conftest.py → test_user fixture sin teardown/cleanup
- conftest.py → pytest_runtest_makereport accede a global browser instance
- utils/helpers.py → GLOBAL_TEST_DATA = {} (estado global mutable)
- utils/helpers.py → get_base_url() duplica lógica de Config
- utils/helpers.py → take_screenshot() duplica funcionalidad de BasePage
- utils/reporter.py → Reimplementa reporter HTML en vez de usar pytest-html/allure
- tests/test_checkout_e2e.py → test_checkout_empty_cart() → try/except para comportamiento esperado
- tests/test_login.py → test_social_login_google() → Retry loop manual dentro del test
