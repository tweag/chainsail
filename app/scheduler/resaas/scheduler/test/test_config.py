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
        "ex_security_groups": ["default", "resaas"],
    },
    "user_code_image": "some-docker-image",
}

VM_NODE_CONFIG_RESAAS_DRIVER = {
    "vm_image_id": "ami-12345",
    "vm_size": "Small",
    "ssh_user": "ubuntu",
    "ssh_public_key": "notARealKey",
    "ssh_private_key_path": "/home/someone/.ssh/key.pem",
    "controller_config_path": "/foo/bar/controller.yaml",
    "storage_config_path": "/foo/bar/storage.yaml",
    "libcloud_provider": "RESAAS_DUMMY",
    "libcloud_driver_inputs": {"creds": "foobar"},
    "user_code_image": "some-docker-image",
}

VALID_CONFIG_VM = {
    "controller": {
        "image": "some-docker-image:latest",
        "ports": [8080, 22],
        "cmd": "bash",
        "args": ["-c", "'echo foo'"],
        "user_code_image": "some-docker-image",
    },
    "worker": {
        "image": "some-docker-image:latest",
        "ports": [22],
        "cmd": "ls",
        "user_code_image": "some-docker-image",
    },
    "node_type": "LibcloudVM",
    "node_config": VM_NODE_CONFIG,
}

VALID_CONFIG_VM_RESAAS_DRIVER = {
    "controller": {
        "image": "some-docker-image:latest",
        "ports": [8080, 22],
        "cmd": "bash",
        "args": ["-c", "'echo foo'"],
        "user_code_image": "some-docker-image",
    },
    "worker": {
        "image": "some-docker-image:latest",
        "ports": [22],
        "cmd": "ls",
        "user_code_image": "some-docker-image",
    },
    "node_type": "LibcloudVM",
    "node_config": VM_NODE_CONFIG_RESAAS_DRIVER,
}

# The below config fails to specify inputs for the driver
CONFIG_INVALID_TYPE = {
    "controller": {
        "image": "some-docker-image:latest",
        "ports": [8080, 22],
        "cmd": "bash",
        "args": ["-c", "'echo foo'"],
        "user_code_image": "some-docker-image",
    },
    "worker": {
        "image": "some-docker-image:latest",
        "ports": [22],
        "cmd": "ls",
        "user_code_image": "some-docker-image",
    },
    "node_type": "DoesNotExist",
    "node_config": VM_NODE_CONFIG,
}


def test_parse_valid_scheduler_config():
    from resaas.scheduler.config import SchedulerConfigSchema

    SchedulerConfigSchema().load(VALID_CONFIG_VM)


def test_parse_scheduler_config_finds_resaas_dummy():
    from resaas.scheduler.config import SchedulerConfigSchema

    config = SchedulerConfigSchema().load(VALID_CONFIG_VM_RESAAS_DRIVER)
    config.node_config.create_node_driver()


def test_create_driver_from_config():
    from resaas.scheduler.config import SchedulerConfigSchema

    config = SchedulerConfigSchema().load(VALID_CONFIG_VM_RESAAS_DRIVER)
    config.node_config.create_node_driver()


def test_parse_scheduler_config_invalid_type():
    from resaas.scheduler.config import SchedulerConfigSchema

    with pytest.raises(ValidationError):
        SchedulerConfigSchema().load(CONFIG_INVALID_TYPE)
