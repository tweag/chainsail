import pytest


def test_parse_job_spec_extra_fields():
    from resaas.scheduler.spec import JobSpecSchema
    from marshmallow.exceptions import ValidationError

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
    from resaas.scheduler.spec import JobSpecSchema

    data = """
    {
        "probability_definition": "gs://bucket/sub/path/script_and_data",
        "max_replicas": 2,
        "initial_schedule_parameters": {
            "minimum_beta": 1,
            "beta_ratio": 0.5
        }
    }
    """
    JobSpecSchema().loads(data)
