from abc import ABC, abstractmethod

# Global for passing runner configurations
runner_config = {}


class AbstractRERunner(ABC):
    """
    Base class for sampling runners.
    """

    @abstractmethod
    def run_sampling(self, storage):
        pass
