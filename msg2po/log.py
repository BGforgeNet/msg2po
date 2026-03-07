# Logging configuration using loguru.
# Call setup_logging() from CLI entry points to set the log level.
# Library code just does: from loguru import logger

import sys
from functools import wraps

from loguru import logger

FORMAT_DEFAULT = "<level>{level: <8}</level> | {message}"
FORMAT_TIMESTAMP = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | {message}"


def setup_logging(verbose: bool = False, quiet: bool = False, timestamps: bool = False) -> None:
    """Configure loguru for CLI use. Call once from main()."""
    logger.remove()

    if quiet:
        level = "WARNING"
    elif verbose:
        level = "DEBUG"
    else:
        level = "INFO"

    fmt = FORMAT_TIMESTAMP if timestamps else FORMAT_DEFAULT
    logger.add(sys.stderr, level=level, format=fmt)


def cli_entry(fn):
    """Decorator for CLI entry points. Catches exceptions and logs them cleanly."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            logger.warning("Interrupted by user")
            sys.exit(1)
        except Exception as e:
            logger.error(f"{type(e).__name__}: {e}")
            logger.opt(exception=True).debug("Full traceback")
            sys.exit(1)

    return wrapper
