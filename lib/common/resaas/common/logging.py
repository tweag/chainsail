"""
Controller logging functionality
"""
import json
from datetime import datetime
import logging
from logging.handlers import MemoryHandler
from math import floor

import requests


class GraphiteHTTPHandler(logging.Handler):
    """A logging handler for writing Graphite events.

    Uses `requests` internally and writes the log record to the Graphite event's
    'data' field. Supports custom logging formaters.

    Args:
        url: The graphite events url
        what: The name of the event
        tags: An optional list of tags to give the event
        timeout: Request timeout in seconds

    """

    def __init__(self, url: str, what="log", tags=None, timeout=5):
        super().__init__()
        self.url = url
        self.timeout = timeout
        self.what = what
        if not tags:
            self.tags = ["log"]
        else:
            self.tags = tags

    def emit(self, record: logging.LogRecord):
        try:
            payload = {
                "what": self.what,
                "tags": self.tags + [record.levelname],
                "when": floor(datetime.utcnow().timestamp()),
                "data": self.format(record),
            }
            response = requests.post(
                url=self.url,
                data=json.dumps(payload),
                timeout=self.timeout,
            )
            response.raise_for_status()
        except Exception:
            self.handleError(record)


def configure_controller_logging(
    log_level,
    remote_logging,
    metrics_address,
    remote_logging_port,
    remote_logging_buffer_size,
    format_string=None,
):
    """
    Configures controller logging.

    Args:
        log_level (str): log level
        remote_logging (bool): whether to enable remote logging
        metrics_address (str): IP address / hostname of remote logging server
        remote_logging_port (int): port on which remote logging server is listening
        remote_logging_buffer_size (int): remote logging buffer size
        format_string (str): format string for the logging formatter
    """
    logger = logging.getLogger("resaas.controller")
    log_level = logging.getLevelName(log_level)
    base_logger = logging.getLogger("resaas")
    base_logger.setLevel(log_level)
    basic_handler = logging.StreamHandler()
    if format_string is None:
        format_string = "[%(levelname)s] %(asctime)s - %(name)s - %(message)s"
    basic_formatter = logging.Formatter(format_string)
    basic_handler.setFormatter(basic_formatter)
    base_logger.addHandler(basic_handler)

    if remote_logging:
        logger.info("Configuring remote logging")

        # Add graphite remote logging
        graphite_handler = GraphiteHTTPHandler(
            url=f"http://{metrics_address}:{remote_logging_port}/events",
            what="log",
            tags=["log"],
        )
        graphite_handler.setFormatter(basic_formatter)
        # Use buffering to avoid having to making excessive calls
        buffered_graphite_handler = MemoryHandler(
            remote_logging_buffer_size, target=graphite_handler
        )
        base_logger.addHandler(buffered_graphite_handler)
