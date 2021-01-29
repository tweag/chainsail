from abc import abstractmethod, ABC


class AbstractRERunner(ABC):
    """
    Base class for sampling runners.
    """

    @abstractmethod
    def run_sampling(self, storage):
        pass
