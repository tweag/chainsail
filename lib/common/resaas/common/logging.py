"""
Controller logging functionality
"""
import json
from datetime import datetime
import logging
from logging.handlers import MemoryHandler
from math import floor

import yaml
import requests

from resaas.common.configs import RemoteLoggingConfigSchema


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

    def __init__(self, url: str, what="log", tags=None, timeout=5, job_id=None):
        super().__init__()
        self.url = url
        self.timeout = timeout
        self.what = what
        if not tags:
            self.tags = ["log"]
        else:
            self.tags = tags
        self.job_id = job_id

    def emit(self, record: logging.LogRecord):
        try:
            if job_id := self.job_id:
                # use job ID attribute
                if record["job_id"] and record["job_id"] != job_id:
                    raise ValueError("Inconsistent job IDs during log emission")
            elif job_id := record["job_id"]:
                # use job ID in log record
                pass
            else:
                # no job id given: don't log to Graphite
                return
            payload = {
                "what": self.what,
                "tags": self.tags + [record.levelname, f"job{job_id}"],
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


def configure_logging(
    logger_name, log_level, remote_logging_config_path, format_string=None, job_id=None
):
    """
    Configures logging.

    Args:
        logger_name(str): logger name; e.g. "resaas.controller"
        log_level (str): log level
        remote_logging_config_path (str): path to remote logging config file
        format_string (str): format string for the logging formatter
        job_id (int): job id
    """
    logger = logging.getLogger(logger_name)
    log_level = logging.getLevelName(log_level)
    base_logger = logging.getLogger("resaas")
    base_logger.setLevel(log_level)
    basic_handler = logging.StreamHandler()
    if format_string is None:
        format_string = f"[%(levelname)s] %(asctime)s - %(name)s - job #%(job_id)s - %(message)s"
    basic_formatter = logging.Formatter(format_string)
    basic_handler.setFormatter(basic_formatter)

    # adds job ID to log record extras
    class JobIDAddingFilter:
        def filter(self, log_record):
            if not hasattr(record, "job_id"):
                log_record.job_id = str(job_id) or "n/a"
            return True

    basic_handler.addFilter(JobIDAddingFilter())
    base_logger.addHandler(basic_handler)

    if remote_logging_config_path:
        logger.info("Configuring remote logging")
        with open(remote_logging_config_path) as f:
            config = RemoteLoggingConfigSchema().load(yaml.safe_load(f))

        # Add graphite remote logging
        graphite_handler = GraphiteHTTPHandler(
            url=f"http://{config.address}:{config.port}/events",
            what="log",
            tags=["log"],
            job_id=job_id,
        )
        graphite_handler.setFormatter(basic_formatter)
        # Use buffering to avoid having to making excessive calls
        buffered_graphite_handler = MemoryHandler(config.buffer_size, target=graphite_handler)

        # don't log debug messages to Graphite - they might contain internal
        # IP addresses / info about the service architecture
        class InfoFilter:
            def filter(self, log_record):
                return log_record.levelno >= logging.INFO

        buffered_graphite_handler.addFilter(InfoFilter())
        buffered_graphite_handler.setFormatter(logging.Formatter(config.format_string))
        base_logger.addHandler(buffered_graphite_handler)
