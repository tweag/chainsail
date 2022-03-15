"""
Utility functions used by multiple modules
"""
import os
import yaml

from chainsail.common.configs import ControllerConfigSchema
from chainsail.scheduler.config import load_scheduler_config

import boto3

scheduler_config = load_scheduler_config()

# FIXME: Results retrieval logic and storage backend logic should be homogenized


def sanitize_object_name(object_name: str) -> str:
    return object_name.strip("/")


def get_s3_client_and_container():
    """Gets the boto3 client and results bucket."""
    s3 = boto3.client(
        "s3",
        endpoint_url=scheduler_config.results_endpoint_url,
        aws_access_key_id=scheduler_config.results_access_key_id,
        aws_secret_access_key=scheduler_config.results_secret_key,
    )

    return s3, scheduler_config.results_bucket


def get_storage_basename():
    controller_config_path = scheduler_config.node_config.controller_config_path
    with open(controller_config_path) as f:
        raw_controller_config = yaml.load(f, Loader=yaml.FullLoader)
    storage_basename = ControllerConfigSchema().load(raw_controller_config).storage_basename
    if storage_basename.startswith("/"):
        storage_basename = storage_basename[1:]

    return storage_basename


def get_job_blob_root(job_id):
    storage_basename = get_storage_basename()
    return os.path.join(storage_basename, str(job_id)) + "/"


def get_signed_url(blob_path, expiry_time, s3=None, container=None):
    if not s3 and not container:
        s3, container = get_s3_client_and_container()
    elif (s3 and not container) or (not s3 and container):
        raise ValueError(
            "Either both 's3' and 'container' have to be given or none of them"
        )
    response = s3.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": container,
            "Key": sanitize_object_name(blob_path),
        },
        # TODO for future me: is boto3 expiry time also in seconds?
        ExpiresIn=expiry_time,
    )

    return response
