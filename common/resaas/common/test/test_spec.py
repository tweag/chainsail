import pytest

from marshmallow.exceptions import ValidationError


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
            "minimum_beta": 1
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


def test_parse_wrong_initial_schedule_params_job_spec():
    from resaas.common.spec import JobSpecSchema

    data = """
    {
        "probability_definition": "gs://bucket/sub/path/script_and_data",
        "initial_schedule_parameters": {
            "minimum_gamma": 1
        }
    }
    """
    with pytest.raises(ValidationError):
        JobSpecSchema().loads(data)
