VALID_CONTROLLER_CONFIG = """
{
    "scheduler_address": "123.2.12.12",
    "scheduler_port": 1001,
    "runner": "some.module:MyRunner"
}

"""


def test_parse_valid_config():
    from resaas.re_job_controller.run import ControllerConfigSchema

    config = ControllerConfigSchema().loads(VALID_CONTROLLER_CONFIG)
