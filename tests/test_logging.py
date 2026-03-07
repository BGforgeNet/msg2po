# Tests for logging configuration.

from loguru import logger

from msg2po.log import setup_logging


class TestSetupLogging:
    def test_default_level_is_info(self, capsys):
        setup_logging()
        logger.debug("should not appear")
        logger.info("should appear")
        captured = capsys.readouterr()
        assert "should not appear" not in captured.err
        assert "should appear" in captured.err

    def test_verbose_shows_debug(self, capsys):
        setup_logging(verbose=True)
        logger.debug("debug message")
        captured = capsys.readouterr()
        assert "debug message" in captured.err

    def test_quiet_hides_info(self, capsys):
        setup_logging(quiet=True)
        logger.info("should not appear")
        logger.warning("should appear")
        captured = capsys.readouterr()
        assert "should not appear" not in captured.err
        assert "should appear" in captured.err
