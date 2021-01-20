from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from marshmallow import Schema, fields, post_load
from marshmallow_enum import EnumField


class Dependencies(ABC):
    """A set of software packages to be installed on a node."""

    @property
    @abstractmethod
    def packages(self) -> str:
        pass

    @property
    @abstractmethod
    def installation_script(self) -> str:
        pass


class PipDependencies(Dependencies):
    """PyPI Python packages"""

    def __init__(self, requirements: List[str]):
        self._packages = requirements

    @property
    def packages(self):
        return self._packages

    @property
    def installation_script(self):
        return f"pip install {' '.join(self.packages)}"


def _load_dep(dep_type: str, pkgs: List[str]):
    if dep_type == DependenciesType.PIP:
        return PipDependencies(pkgs)
    else:
        raise ValueError(f"Unknown dependency type: {dep_type}")


class DependenciesType(Enum):
    PIP = "pip"


class DependencySchema(Schema):
    type = EnumField(DependenciesType, by_value=True)
    deps = fields.List(fields.String())

    @post_load
    def make_dependencies(self, data, **kwargs):
        return _load_dep(data["type"], data["deps"])


@dataclass
class DistributionSchedule:
    minimum_beta: float
    beta_ratio: float


class DistributionScheduleSchema(Schema):
    minimum_beta = fields.Float()
    beta_ratio = fields.Float()

    @post_load
    def make_dist_schedule(self, data, **kwargs):
        return DistributionSchedule(**data)


class TemperedDistributionFamily(Enum):
    BOLTZMANN = "boltzmann"


class JobSpecSchema(Schema):
    probability_definition = fields.String(required=True)
    initial_number_of_replicas = fields.Int()
    initial_schedule_parameters = fields.Nested(DistributionScheduleSchema)
    max_replicas = fields.Int()
    tempered_dist_family = EnumField(TemperedDistributionFamily, by_value=True)
    dependencies = fields.List(fields.Nested(DependencySchema))

    @post_load
    def make_job_spec(self, data, **kwargs):
        return JobSpec(**data)


class JobSpec:
    def __init__(
        self,
        probability_definition: str,
        initial_number_of_replicas: int = 10,
        initial_schedule_parameters: Optional[DistributionSchedule] = None,
        max_replicas: int = 100,
        tempered_dist_family: TemperedDistributionFamily = TemperedDistributionFamily.BOLTZMANN,
        dependencies: Optional[Dependencies] = None,
    ):
        self.probability_definition = probability_definition
        self.initial_number_of_replicas = initial_number_of_replicas
        self.max_replicas = max_replicas
        self.tempered_dist_family = tempered_dist_family
        # TODO: Confirm these default values
        if initial_schedule_parameters is None:
            self.initial_schedule_parameters = DistributionSchedule(1.0, 0.5)
        else:
            self.initial_schedule_parameters = initial_number_of_replicas
        if dependencies is None:
            self.dependencies = []
        else:
            self.dependencies = dependencies
