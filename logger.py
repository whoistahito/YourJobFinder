from __future__ import annotations

from itertools import cycle
import logging
from markdownify import markdownify as md
import numpy as np
import re
import requests


def create_logger(name: str):
    logger = logging.getLogger(f"Your Job Finder:{name}")
    logger.propagate = False
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        console_handler = logging.StreamHandler()
        format = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        formatter = logging.Formatter(format)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    return logger
