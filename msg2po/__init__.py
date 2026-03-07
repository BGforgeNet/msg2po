# Replace loguru's default handler with our format.
# This runs before any other module in the package, ensuring consistent output.
import sys

from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO", format="<level>{level: <8}</level> | {message}")
