from resaas.scheduler.nodes.base import NodeType
from resaas.scheduler.nodes.vm import VMNode

# Map node types to node implementations. In the case
# of vm node the details on the driver, etc. are expected
# to exist in the scheduler configuration.
NODE_CLS_REGISTRY = {NodeType.LIBCLOUD_VM: VMNode}
