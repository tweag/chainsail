import pytest
from marshmallow.exceptions import ValidationError

VALID_CONFIG = """
{
    "ssh_public_key": "notARealKey",
    "node_type": "LibcloudVM",
    "node_driver": "gce",
    "driver_specs": {
        "gce": {
            "user_id": "worker@resaas-demo.iam.gserviceaccount.com",
            "key": "./home/user/my-key.json",
            "project": "resaas-demo",
            "datacenter": "us-central1-a"
        }
    }
}
"""

# The below config fails to specify inputs for the driver
INVALID_CONFIG_MISSING_SPECS = """
{
    "ssh_public_key": "notARealKey",
    "node_type": "LibcloudVM",
    "node_driver": "gce",
    "driver_specs": {}
}
"""

# The below config specifies an unknown driver
INVALID_CONFIG_UNKNOWN_DRIVER = """
{
    "ssh_public_key": "notARealKey",
    "node_type": "LibcloudVM",
    "node_driver": "does not exist",
    "driver_specs": {}
}
"""


def test_parse_valid_scheduler_config():
    from resaas.scheduler.config import SchedulerConfigSchema

    SchedulerConfigSchema().loads(VALID_CONFIG)


def test_parse_valid_scheduler_missing_driver_spec():
    from resaas.scheduler.config import SchedulerConfigSchema

    with pytest.raises(ValidationError):
        SchedulerConfigSchema().loads(INVALID_CONFIG_MISSING_SPECS)


def test_parse_valid_scheduler_unknown_driver():
    from resaas.scheduler.config import SchedulerConfigSchema

    with pytest.raises(ValidationError):
        SchedulerConfigSchema().loads(INVALID_CONFIG_UNKNOWN_DRIVER)
