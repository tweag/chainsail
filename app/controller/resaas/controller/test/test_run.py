VALID_CONTROLLER_CONFIG = """
{
    "scheduler_address": "123.2.12.12",
    "scheduler_port": 1001,
    "metrics_address": "127.0.0.1",
    "metrics_port": 2004,
    "runner": "some.module:MyRunner",
    "remote_logging_config": "/this/is/my/favorite/path.yaml"
}

"""


def test_parse_valid_config():
    from resaas.controller.run import ControllerConfigSchema

    config = ControllerConfigSchema().loads(VALID_CONTROLLER_CONFIG)
