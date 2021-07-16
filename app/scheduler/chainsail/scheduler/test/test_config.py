import pytest
from marshmallow.exceptions import ValidationError

VM_NODE_CONFIG = {
    "vm_image_id": "ami-12345",
    "vm_size": "Small",
    "ssh_user": "ubuntu",
    "ssh_public_key": "notARealKey",
    "ssh_private_key_path": "/home/someone/.ssh/key.pem",
    "controller_config_path": "/foo/bar/controller.yaml",
    "storage_config_path": "/foo/bar/storage.yaml",
    "libcloud_provider": "EC2",
    "libcloud_driver_inputs": {
        "key": "XXXXXXXXXXX",
        "secret": "XXXXXXXXXXX",
        "ex_security_groups": ["default", "chainsail"],
    },
}

VM_NODE_CONFIG_CHAINSAIL_DRIVER = {
    "vm_image_id": "ami-12345",
    "vm_size": "Small",
    "ssh_user": "ubuntu",
    "ssh_public_key": "notARealKey",
    "ssh_private_key_path": "/home/someone/.ssh/key.pem",
    "controller_config_path": "/foo/bar/controller.yaml",
    "storage_config_path": "/foo/bar/storage.yaml",
    "libcloud_provider": "CHAINSAIL_DUMMY",
    "libcloud_driver_inputs": {"creds": "foobar"},
}

VALID_CONFIG_VM = {
    "controller": {
        "image": "some-docker-image:latest",
        "ports": [8080, 22],
        "cmd": "bash",
        "args": ["-c", "'echo foo'"],
        "user_code_image": "some-docker-image",
        "httpstan_image": "another-docker-image",
    },
    "worker": {
        "image": "some-docker-image:latest",
        "ports": [22],
        "cmd": "ls",
        "user_code_image": "some-docker-image",
        "httpstan_image": "another-docker-image",
    },
    "node_type": "LibcloudVM",
    "node_config": VM_NODE_CONFIG,
    "results_url_expiry_time": 42,
    "remote_logging_config_path": "/I/am/some/path",
}

VALID_CONFIG_VM_CHAINSAIL_DRIVER = {
    "controller": {
        "image": "some-docker-image:latest",
        "ports": [8080, 22],
        "cmd": "bash",
        "args": ["-c", "'echo foo'"],
        "user_code_image": "some-docker-image",
        "httpstan_image": "another-docker-image",
    },
    "worker": {
        "image": "some-docker-image:latest",
        "ports": [22],
        "cmd": "ls",
        "user_code_image": "some-docker-image",
        "httpstan_image": "another-docker-image",
    },
    "node_type": "LibcloudVM",
    "node_config": VM_NODE_CONFIG_CHAINSAIL_DRIVER,
    "results_url_expiry_time": 42,
    "remote_logging_config_path": "/I/am/some/path",
}

# The below config fails to specify inputs for the driver
CONFIG_INVALID_TYPE = {
    "controller": {
        "image": "some-docker-image:latest",
        "ports": [8080, 22],
        "cmd": "bash",
        "args": ["-c", "'echo foo'"],
        "user_code_image": "some-docker-image",
        "httpstan_image": "another-docker-image",
    },
    "worker": {
        "image": "some-docker-image:latest",
        "ports": [22],
        "cmd": "ls",
        "user_code_image": "some-docker-image",
        "httpstan_image": "another-docker-image",
    },
    "node_type": "DoesNotExist",
    "node_config": VM_NODE_CONFIG,
    "results_url_expiry_time": 42,
    "remote_logging_config_path": "/I/am/some/path",
}


def test_parse_valid_scheduler_config():
    from chainsail.scheduler.config import SchedulerConfigSchema

    SchedulerConfigSchema().load(VALID_CONFIG_VM)


def test_parse_scheduler_config_finds_chainsail_dummy():
    from chainsail.scheduler.config import SchedulerConfigSchema

    config = SchedulerConfigSchema().load(VALID_CONFIG_VM_CHAINSAIL_DRIVER)
    config.node_config.create_node_driver()


def test_create_driver_from_config():
    from chainsail.scheduler.config import SchedulerConfigSchema

    config = SchedulerConfigSchema().load(VALID_CONFIG_VM_CHAINSAIL_DRIVER)
    config.node_config.create_node_driver()


def test_parse_scheduler_config_invalid_type():
    from chainsail.scheduler.config import SchedulerConfigSchema

    with pytest.raises(ValidationError):
        SchedulerConfigSchema().load(CONFIG_INVALID_TYPE)
