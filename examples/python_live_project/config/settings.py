import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    BASE_URL = os.getenv("BASE_URL", "https://ecommerce-demo.testapp.io")
    API_BASE_URL = os.getenv("API_BASE_URL", "https://api.ecommerce-demo.testapp.io/v1")
    
    # BAD PRACTICE: Hardcoded credentials in config
    ADMIN_USERNAME = "admin@testapp.io"
    ADMIN_PASSWORD = "Admin123!@#"
    
    # BAD PRACTICE: More hardcoded credentials
    DB_HOST = "db-prod-replica.testapp.io"
    DB_USER = "test_automation"
    DB_PASSWORD = "t3st_p@ss_2024"
    
    API_KEY = "sk-live-abc123def456ghi789jkl012mno345"
    
    TIMEOUT = 30000
    RETRY_COUNT = 3
    SCREENSHOT_ON_FAILURE = True
    VIDEO_ON_FAILURE = True
    
    BROWSER = os.getenv("BROWSER", "chromium")
    HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
    SLOW_MO = int(os.getenv("SLOW_MO", "0"))
    
    REPORT_DIR = "reports"
    SCREENSHOT_DIR = "reports/screenshots"
    VIDEO_DIR = "reports/videos"


class StagingConfig(Config):
    BASE_URL = "https://staging.ecommerce-demo.testapp.io"
    API_BASE_URL = "https://staging-api.ecommerce-demo.testapp.io/v1"


class ProductionConfig(Config):
    # BAD PRACTICE: Running tests against production
    BASE_URL = "https://www.ecommerce-demo.testapp.io"
    API_BASE_URL = "https://api.ecommerce-demo.testapp.io/v1"


def get_config(env=None):
    env = env or os.getenv("TEST_ENV", "staging")
    configs = {
        "staging": StagingConfig,
        "production": ProductionConfig,
    }
    return configs.get(env, Config)()
