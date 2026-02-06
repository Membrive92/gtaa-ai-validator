"""
Tests for gtaa_validator.logging_config

Covers:
- Handler creation (console always present)
- Verbose vs non-verbose log levels
- File handler creation when log_file is provided
- Handler deduplication on repeated calls
"""

import logging
import os
import shutil
import tempfile

from gtaa_validator.logging_config import setup_logging


class TestSetupLogging:
    """Tests for setup_logging()."""

    def _get_logger(self):
        return logging.getLogger("gtaa_validator")

    def teardown_method(self):
        """Clean up handlers after each test."""
        logger = self._get_logger()
        logger.handlers.clear()

    def test_creates_console_handler(self):
        """setup_logging() always creates a console StreamHandler."""
        setup_logging(verbose=False)
        logger = self._get_logger()
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.StreamHandler)

    def test_verbose_sets_debug_level(self):
        """With verbose=True, console handler level is DEBUG."""
        setup_logging(verbose=True)
        logger = self._get_logger()
        console = logger.handlers[0]
        assert console.level == logging.DEBUG

    def test_non_verbose_sets_warning_level(self):
        """With verbose=False, console handler level is WARNING."""
        setup_logging(verbose=False)
        logger = self._get_logger()
        console = logger.handlers[0]
        assert console.level == logging.WARNING

    def test_file_handler_created(self):
        """When log_file is provided, a FileHandler is added."""
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
            log_path = f.name
        try:
            setup_logging(verbose=False, log_file=log_path)
            logger = self._get_logger()
            assert len(logger.handlers) == 2
            file_handler = logger.handlers[1]
            assert isinstance(file_handler, logging.FileHandler)
            assert file_handler.level == logging.DEBUG
        finally:
            # Close handler before deleting
            for h in logger.handlers:
                if isinstance(h, logging.FileHandler):
                    h.close()
            os.unlink(log_path)

    def test_no_file_handler_without_log_file(self):
        """Without log_file, only console handler exists."""
        setup_logging(verbose=True)
        logger = self._get_logger()
        assert len(logger.handlers) == 1

    def test_deduplication_on_repeated_calls(self):
        """Calling setup_logging() twice does not duplicate handlers."""
        setup_logging(verbose=False)
        setup_logging(verbose=True)
        logger = self._get_logger()
        assert len(logger.handlers) == 1

    def test_logger_level_is_debug(self):
        """Root gtaa_validator logger level is always DEBUG."""
        setup_logging(verbose=False)
        logger = self._get_logger()
        assert logger.level == logging.DEBUG

    def test_file_handler_writes_log(self):
        """FileHandler actually writes log messages to disk."""
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
            log_path = f.name
        try:
            setup_logging(verbose=False, log_file=log_path)
            logger = self._get_logger()
            logger.info("Test message for file")
            # Flush handlers
            for h in logger.handlers:
                h.flush()
            with open(log_path, encoding="utf-8") as f:
                content = f.read()
            assert "Test message for file" in content
        finally:
            for h in logger.handlers:
                if isinstance(h, logging.FileHandler):
                    h.close()
            os.unlink(log_path)

    def test_auto_creates_parent_directory(self):
        """FileHandler auto-creates parent directories if they don't exist."""
        tmp_dir = tempfile.mkdtemp()
        log_path = os.path.join(tmp_dir, "subdir", "nested", "debug.log")
        try:
            setup_logging(verbose=False, log_file=log_path)
            logger = self._get_logger()
            logger.info("Auto-created directory test")
            for h in logger.handlers:
                h.flush()
            assert os.path.exists(log_path)
            with open(log_path, encoding="utf-8") as f:
                content = f.read()
            assert "Auto-created directory test" in content
        finally:
            for h in logger.handlers:
                if isinstance(h, logging.FileHandler):
                    h.close()
            shutil.rmtree(tmp_dir)
