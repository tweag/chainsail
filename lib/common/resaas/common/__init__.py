"""
Code shared between different parts of Chainsail.
"""
import logging
import sys

import numpy as np
from typing import Tuple

from chainsail.common.custom_logging import NO_JOB_ID
from chainsail.common.pdfs import AbstractPDF


def import_from_user(job_id=None) -> Tuple[AbstractPDF, np.ndarray]:
    """
    Imports a user-defined pdf and corresponding initial states from
    module `probability`.
    """
    try:
        from probability import initial_states, pdf
    except ImportError as e:
        logger = logging.getLogger("chainsail.controller")
        logger.exception(
            "Failed to import user-defined pdf and initial_states. Does "
            "the `probability` module exist on the PYTHONPATH? "
            f"PYTHONPATH={sys.path}",
            extra={"job_id": job_id or NO_JOB_ID},
        )
        raise e
    return (pdf, initial_states)
