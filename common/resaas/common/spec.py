from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Union

from marshmallow import Schema, fields, post_load
from marshmallow_enum import EnumField
from marshmallow.exceptions import ValidationError


class DependenciesType(Enum):
    PIP = "pip"


class Dependencies(ABC):
    """A set of software packages to be installed on a node."""

    @property
    @abstractmethod
    def type(self) -> DependenciesType:
        pass

    @property
    @abstractmethod
    def packages(self) -> str:
        pass

    @property
    @abstractmethod
    def installation_script(self) -> str:
        pass

    def __eq__(self, other) -> bool:
        return self.type == other.type and self.packages == other.packages


class PipDependencies(Dependencies):
    """PyPI Python packages"""

    def __init__(self, requirements: List[str]):
        self._packages = requirements
    
    @property
    def type(self) -> DependenciesType:
        return DependenciesType.PIP

    @property
    def packages(self):
        return self._packages

    @property
    def installation_script(self):
        if self.packages:
            return f"pip install {' '.join(self.packages)}"
        else:
            return ""


def _load_dep(dep_type: str, pkgs: List[str]):
    if dep_type == DependenciesType.PIP:
        return PipDependencies(pkgs)
    else:
        raise ValueError(f"Unknown dependency type: {dep_type}")



class DependencySchema(Schema):
    type = EnumField(DependenciesType, by_value=True)
    packages = fields.List(fields.String(), data_key="deps")

    @post_load
    def make_dependencies(self, data, **kwargs):
        print(data)
        if data:
            return _load_dep(data["type"], data["packages"])


class LocalSamplers(Enum):
    NAIVE_HMC = "naive_hmc"


@dataclass
class NaiveHMCParameters:
    n_steps: int = 20
    timesteps: Optional[str] = None
    timestep_adaption_limit: Optional[int] = None
    adaption_uprate: float = 1.05
    adaption_downrate: float = 0.95


class OptimizationQuantity(Enum):
    ACCEPTANCE_RATE = "acceptance_rate"


@dataclass
class OptimizationParameters:
    optimization_quantity_target: float = 0.2
    optimization_quantity: OptimizationQuantity = OptimizationQuantity.ACCEPTANCE_RATE
    decrement: float = 0.01
    max_param: float = 1.0
    min_param: float = 0.01
    max_optimization_runs: int = 5


@dataclass
class ReplicaExchangeParameters:
    num_production_samples: int = 2000
    num_optimization_samples: int = 5000
    dump_interval: int = 1000
    dump_step: int = 5
    swap_interval: int = 5
    statistics_update_interval: int = 50
    status_interval: int = 100


@dataclass
class BoltzmannInitialScheduleParameters:
    minimum_beta: float


class ReplicaExchangeParametersSchema(Schema):
    num_production_samples = fields.Int()
    num_optimization_samples = fields.Int()
    dump_interval = fields.Int()
    dump_step = fields.Int()
    swap_interval = fields.Int()
    statistics_update_interval = fields.Int()
    status_interval = fields.Int()

    @post_load
    def make_replica_exchange_parameters(self, data, **kwargs):
        return ReplicaExchangeParameters(**data)


class OptimizationParametersSchema(Schema):
    optimization_quantity = EnumField(OptimizationQuantity, by_value=True)
    optimization_quantity_target = fields.Float()
    decrement = fields.Float()
    max_param = fields.Float()
    min_param = fields.Float()
    max_optimization_runs = fields.Int()

    @post_load
    def make_optimization_parameters(self, data, **kwargs):
        return OptimizationParameters(**data)


class NaiveHMCParametersSchema(Schema):
    n_steps = fields.Int()
    timesteps = fields.Str()
    timestep_adaption_limit = fields.Int()
    adaption_uprate = fields.Float()
    adaption_downrate = fields.Float()

    @post_load
    def make_hmc_sampling_parameters(self, data, **kwargs):
        return NaiveHMCParameters(**data)


class TemperedDistributionFamily(Enum):
    BOLTZMANN = "boltzmann"


class BoltzmannInitialScheduleParametersSchema(Schema):
    minimum_beta = fields.Float()

    @post_load
    def make_boltzmann_initial_schedule_parameters(self, data, **kwargs):
        return BoltzmannInitialScheduleParameters(**data)


INITIAL_SCHEDULE_PARAMETERS_SCHEMAS = {
    TemperedDistributionFamily.BOLTZMANN: BoltzmannInitialScheduleParametersSchema
    }


LOCAL_SAMPLING_PARAMETER_SCHEMAS = {
    LocalSamplers.NAIVE_HMC: NaiveHMCParametersSchema
    }


class JobSpecSchema(Schema):
    probability_definition = fields.String(required=True)
    name = fields.String()
    initial_number_of_replicas = fields.Int()
    initial_schedule_parameters = fields.Dict(fields.String, fields.Float())
    optimization_parameters = fields.Nested(OptimizationParametersSchema)
    replica_exchange_parameters = fields.Nested(ReplicaExchangeParametersSchema)
    hmc_parameters = fields.Nested(NaiveHMCParametersSchema)
    max_replicas = fields.Int()
    tempered_dist_family = EnumField(TemperedDistributionFamily, by_value=True)
    dependencies = fields.Nested(DependencySchema(many=True))

    @post_load
    def make_job_spec(self, data, **kwargs):
        tempered_dist_family = data.get("tempered_dist_family", TemperedDistributionFamily.BOLTZMANN)
        if "initial_schedule_parameters" in data:
            init_sched_params = data["initial_schedule_parameters"]
            if tempered_dist_family == TemperedDistributionFamily.BOLTZMANN:
                init_sched_schema = INITIAL_SCHEDULE_PARAMETERS_SCHEMAS[TemperedDistributionFamily.BOLTZMANN]()
                init_sched_schema.load(init_sched_params)
                init_sched_params = init_sched_schema.make_boltzmann_initial_schedule_parameters(init_sched_params)

            data['initial_schedule_parameters'] = init_sched_params

        return JobSpec(**data)


class JobSpec:
    def __init__(
        self,
        probability_definition: str,
        name: Optional[str] = None,
        initial_number_of_replicas: int = 15,
        initial_schedule_parameters: Optional[Union[BoltzmannInitialScheduleParameters, ]] = BoltzmannInitialScheduleParameters(0.01),
        optimization_parameters: Optional[OptimizationParameters] = OptimizationParameters(),
        replica_exchange_parameters: Optional[ReplicaExchangeParameters] = ReplicaExchangeParameters(),
        local_sampling_parameters: Optional[NaiveHMCParameters] = NaiveHMCParameters(),
        max_replicas: int = 100,
        tempered_dist_family: TemperedDistributionFamily = TemperedDistributionFamily.BOLTZMANN,
        dependencies: Optional[Dependencies] = None,
    ):
        self.probability_definition = probability_definition
        self.name = name
        self.initial_number_of_replicas = initial_number_of_replicas
        self.max_replicas = max_replicas
        self.tempered_dist_family = tempered_dist_family
        if initial_schedule_parameters is None:
            self.initial_schedule_parameters = BoltzmannInitialScheduleParameters(0.01)
        else:
            self.initial_schedule_parameters = initial_schedule_parameters
        if optimization_parameters is None:
            self.optimization_parameters = OptimizationParameters()
        else:
            self.optimization_parameters = optimization_parameters
        if replica_exchange_parameters is None:
            self.replica_exchange_parameters = ReplicaExchangeParameters()
        else:
            self.replica_exchange_parameters = replica_exchange_parameters
        if local_sampling_parameters is None:
            self.local_sampling_parameters = NaiveHMCParameters()
        else:
            self.local_sampling_parameters = local_sampling_parameters
        if dependencies is None:
            self.dependencies = []
        else:
            self.dependencies = dependencies

    def __eq__(self, other: "JobSpec") -> bool:
        return all([
                self.probability_definition == other.probability_definition,
                self.initial_number_of_replicas == other.initial_number_of_replicas,
                self.initial_schedule_parameters == other.initial_schedule_parameters,
                self.max_replicas == other.max_replicas,
                self.tempered_dist_family == other.tempered_dist_family,
                self.dependencies == other.dependencies
            ]
        )
