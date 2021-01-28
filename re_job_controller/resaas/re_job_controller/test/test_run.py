VALID_CONTROLLER_CONFIG = """
{
    "scheduler_address": "123.2.12.12",
    "scheduler_port": 1001,
    "storage_backend": "cloud",
    "storage_backend_config": {
        "local": {},
        "cloud": {
            "libcloud_provider": "S3",
            "container_name": "foobar",
            "driver_kwargs": {
                "key": "xxxxxx",
                "secret": "xxxxxx"
            }
        }
    }
}

"""


def test_parse_valid_config():
    from resaas.re_job_controller.run import ControllerConfigSchema

    config = ControllerConfigSchema().loads(VALID_CONTROLLER_CONFIG)
