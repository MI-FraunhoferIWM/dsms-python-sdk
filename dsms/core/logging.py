"""DSMS logging module"""

import logging
import sys

LOG_FORMAT = "[%(asctime)s - %(name)s - %(levelname)s]: %(message)s"
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(LOG_FORMAT)
handler.setFormatter(formatter)
