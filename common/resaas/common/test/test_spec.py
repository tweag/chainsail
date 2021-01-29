import pytest


def test_pip_deps_eq():
    from resaas.common.spec import PipDependencies

    dep_1 = PipDependencies(["numpy>1.15", "scipy"])
    dep_2 = PipDependencies(["numpy>1.15", "scipy"])

    assert dep_1 == dep_2

def test_pip_deps_not_eq():
    from resaas.common.spec import PipDependencies

    dep_1 = PipDependencies(["tensorflow", "scipy"])
    dep_2 = PipDependencies(["numpy>1.15", "scipy"])

    assert not (dep_1 == dep_2)



def test_spec_eq():
    from resaas.common.spec import JobSpec, PipDependencies

    spec_1 = JobSpec("foo/bar")
    spec_2 = JobSpec("foo/bar")

    assert spec_1 == spec_2


def test_spec_not_eq():
    from resaas.common.spec import JobSpec, PipDependencies

    spec_1 = JobSpec("foo/bar")
    spec_2 = JobSpec("other")

    assert not (spec_1 == spec_2)


def test_parse_job_spec_extra_fields():
    from marshmallow.exceptions import ValidationError

    from resaas.common.spec import JobSpecSchema

    data = """
    {
        "probability_definition": "gs://bucket/sub/path/script_and_data",
        "max_replicas": 2,
        "unknown_data": "DROP TABLE;"
    }
    """
    with pytest.raises(ValidationError):
        JobSpecSchema().loads(data)


def test_parse_partial_job_spec():
    from resaas.common.spec import JobSpecSchema

    data = """
    {
        "probability_definition": "gs://bucket/sub/path/script_and_data",
        "max_replicas": 2,
        "initial_schedule_parameters": {
            "minimum_beta": 1,
            "beta_ratio": 0.5
        },
        "dependencies": [
            {
                "type": "pip",
                "deps": ["numpy==1.19.5", "pandas==1.0.0"]
            }
        ]
    }
    """
    JobSpecSchema().loads(data)


def test_parse_job_spec_empty_dependencies():
    from resaas.common.spec import JobSpecSchema

    data = """
    {
        "probability_definition": "gs://bucket/sub/path/script_and_data",
        "max_replicas": 2,
        "initial_schedule_parameters": {
            "minimum_beta": 1,
            "beta_ratio": 0.5
        },
        "dependencies": []
    }
    """
    schema = JobSpecSchema()
    spec = schema.loads(data)
    assert spec.dependencies == []


def test_job_spec_serialization_round_trip():
    from resaas.common.spec import JobSpecSchema

    data = """
    {
        "probability_definition": "gs://bucket/sub/path/script_and_data",
        "max_replicas": 2,
        "initial_schedule_parameters": {
            "minimum_beta": 1,
            "beta_ratio": 0.5
        },
        "dependencies": [
            {
                "type": "pip",
                "deps": ["numpy==1.19.5", "pandas==1.0.0"]
            }
        ]
    }
    """
    schema = JobSpecSchema()
    spec_1 = schema.loads(data)
    spec_2 = schema.loads(schema.dumps(spec_1))
    assert spec_1 == spec_2
