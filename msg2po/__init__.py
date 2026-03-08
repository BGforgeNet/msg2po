# Package initialization: configure logging format and PO wrapping.
# This runs before any other module in the package.
import sys

from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO", format="<level>{level: <8}</level> | {message}")

# Patch polib wrapping to match Weblate's translate-toolkit output exactly.
# Without this, every PO roundtrip produces wrapping-only diffs.
# See po_wrap.py for version details and upgrade instructions.
from msg2po.po_wrap import apply_to_polib  # noqa: E402

apply_to_polib()
