"""
Code shared between different parts of RESAAS.
"""
import numpy as np
from typing import Tuple

from resaas.common.pdfs import AbstractPDF


def import_from_user() -> Tuple[AbstractPDF, np.ndarray]:
    """
    Imports a user-defined pdf and corresponding initial states from
    module `probability`.
    """
    try:
        from probability import initial_states, pdf
    except ImportError as e:
        logger.exception(
            "Failed to import user-defined pdf and initial_states. Does "
            "the `probability` module exist on the PYTHONPATH? "
            f"PYTHONPATH={sys.path}"
        )
        raise e
    return (pdf, initial_states)
