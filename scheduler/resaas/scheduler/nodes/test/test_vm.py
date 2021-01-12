from unittest.mock import patch
import os


@patch("libcloud.compute.ssh.SSHClient")
def test_libcloud_vm(mock_ssh_client):

    # from libcloud.compute.drivers.libvirt_driver import LibvirtNodeDriver
    from libcloud.compute.drivers.dummy import DummyNodeDriver

    #   from libcloud.compute.drivers.gce import GCENodeDriver
    from libcloud.compute.base import NodeSize
    from resaas.scheduler.jobs.spec import Dependencies
    from resaas.scheduler.nodes import vm

    driver = DummyNodeDriver(creds="foo")
    node = vm.VMNode(
        "test",
        driver=driver,
        size=driver.list_sizes()[0],
        image=driver.list_images()[0],
        deps=[],
        entrypoint="docker run -d alpine bash -c 'echo foo'",
        ssh_key="abcd123",
    )
    node.create()
    print(node)
