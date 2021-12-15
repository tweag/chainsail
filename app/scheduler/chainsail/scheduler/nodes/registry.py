from chainsail.scheduler.nodes.base import NodeType
from chainsail.scheduler.nodes.vm import VMNode
from chainsail.scheduler.nodes.k8s_pod import K8sNode

# Map node types to node implementations. In the case
# of vm node the details on the driver, etc. are expected
# to exist in the scheduler configuration.
NODE_CLS_REGISTRY = {NodeType.LIBCLOUD_VM: VMNode, NodeType.KUBERNETES_POD: K8sNode}
