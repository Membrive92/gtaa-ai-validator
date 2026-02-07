# 🧪 EcommerceApp Test Automation Framework

Playwright-based test automation framework for the EcommerceApp demo platform. Supports E2E UI testing, API testing, and custom reporting.

## 📁 Project Structure

```
automation_project/
├── config/
│   └── settings.py          # Environment configuration
├── pages/                    # Page Object Model
│   ├── base_page.py          # Base page object
│   ├── login_page.py         # Login page
│   ├── products_page.py      # Products listing page
│   ├── product_detail_page.py # Product detail page
│   ├── cart_page.py           # Shopping cart page
│   ├── checkout_page.py       # Checkout page
│   └── dashboard_page.py     # User dashboard page
├── tests/                    # Test suites
│   ├── test_login.py         # Login tests
│   ├── test_products.py      # Product tests
│   ├── test_cart.py           # Cart tests
│   ├── test_checkout_e2e.py   # E2E checkout flow tests
│   ├── test_dashboard.py     # Dashboard/profile tests
│   └── test_api.py           # API tests
├── api/
│   ├── client.py             # API client
│   └── schemas.py            # JSON schemas for validation
├── utils/
│   ├── helpers.py            # Utility functions
│   └── reporter.py           # Custom HTML/JSON report generator
├── data/
│   └── test_data.json        # Test data
├── reports/                  # Generated reports & screenshots
├── conftest.py               # Pytest fixtures
├── pyproject.toml            # Project dependencies
└── .env.example              # Environment variables template
```

## 🚀 Setup

```bash
# Install dependencies
pip install -e .

# Install Playwright browsers
playwright install chromium

# Copy env config
cp .env.example .env
```

## ▶️ Running Tests

```bash
# Run all tests
pytest

# Run smoke tests only
pytest -m smoke

# Run API tests
pytest -m api

# Run E2E tests
pytest -m e2e

# Run with HTML report
pytest --html=reports/report.html

# Run specific test file
pytest tests/test_login.py -v

# Run in headed mode
HEADLESS=false pytest tests/test_login.py
```

## 📊 Reports

- **HTML Reports**: Generated in `reports/` directory
- **JSON Reports**: Custom JSON reports via `ReportGenerator`
- **Screenshots**: Automatically captured on failure in `reports/screenshots/`
- **Allure**: Configured for allure report generation

## 🏗️ Architecture

The framework follows the **Page Object Model (POM)** pattern:
- Each page is represented by a class in `pages/`
- `BasePage` provides common methods inherited by all pages
- Tests interact with pages through their public methods
- API testing is supported via `api/client.py`

## 🔧 Configuration

Environment-specific configs are managed through `config/settings.py` with support for:
- Staging
- Production
- Custom environments via `TEST_ENV` env variable
