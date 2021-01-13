"""
Utilities for loading and constructing node objects with
their appropriate type.
"""

from resaas.scheduler.nodes.base import Node, NodeType
from resaas.scheduler.nodes.vm import VMNode
from resaas.scheduler.db import TblNodes

# Map node types to node implementations. In the case
# of vm node the details on the driver, etc. are expected
# to exist in the scheduler configuration.
NODE_CLS_REGISTRY = {NodeType.LIBCLOUD_VM: VMNode}


def load_from_table(tbl: TblNodes):
    """Looks the class for a given node type and calls its factory method"""
    cls = NODE_CLS_REGISTRY[NodeType(tbl.node_type)]
    return cls.from_representation()
