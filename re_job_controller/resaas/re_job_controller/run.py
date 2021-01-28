"""
Main entrypoint to the resaas controller
"""

from multiprocessing import Process
from typing import Tuple


ProcessStatus = Tuple[bool, str]


def check_status(proc: Process) -> ProcessStatus:
    # TODO: This will be called via gRPC
    pass


def run():
    # TODO: Load jobspec from file

    # Initialize controller
    # controller = Controller.from_spec(...)
    # Start controller in another process
    # Poll that process until it exits
    controller = None
    controller_proc = Process(target=controller.run, daemon=True)
    controller_proc.start()

    # TODO: Bind gRPC endpoint to a function which checks whether
    #   controller_proc is still alive. If it is not alive, then
    #   we need to see if any exceptions were raised.

    # TODO: Await controller_proc, then teardown gRPC server gracefully
    pass


if __name__ == "__main__":
    run()
