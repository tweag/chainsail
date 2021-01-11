from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import List


class Dependency(ABC):
    @property
    @abstractmethod
    def DEP_TYPE(self) -> str:
        pass

    @property
    @abstractmethod
    def packages(self) -> str:
        pass

    @property
    @abstractmethod
    def installation_script(self) -> str:
        pass


class PipDependency(Dependency):
    DEP_TYPE = "pip"

    def __init__(self, requirements: List[str]):
        self._packages = requirements

    @property
    def packages(self):
        return self._packages

    @property
    def installation_script(self):
        return [f"pip install {' '.join(self.packages)}"]


@dataclass
class JobSpec:
    dependencies: List[Dependency]
