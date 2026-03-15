from collections import defaultdict, deque

from loguru import logger

from crunge import imnodes

from .node import Node
from .wire import Wire

class GraphLayout:
    def place_node_right_of(self, anchor: Node, node: Node, gap_x: float = 40.0, gap_y: float = 0.0):
        x, y = anchor.position
        width, height = anchor.size
        node.position = (x + width + gap_x, y + gap_y)

    def place_children_right(
        self,
        anchor: Node,
        children: list[Node],
        gap_x: float = 40.0,
        gap_y: float = 20.0,
    ):
        if not children:
            return

        parent_x, parent_y = anchor.position
        parent_width, parent_height = anchor.size

        child_sizes: list[tuple[Node, float, float]] = []
        for child in children:
            child_width, child_height = child.size
            child_sizes.append((child, child_width, child_height))

        total_height = sum(height for _, _, height in child_sizes)
        total_height += gap_y * (len(child_sizes) - 1)

        start_y = parent_y + (parent_height - total_height) / 2.0
        x = parent_x + parent_width + gap_x

        current_y = start_y
        for child, child_width, child_height in child_sizes:
            logger.debug(f"Placing child node {child.id} at ({x}, {current_y})")
            child.position = (x, current_y)
            current_y += child_height + gap_y

    """
    def place_children_right(
        self,
        anchor: Node,
        children: list[Node],
        gap_x: float = 40.0,
        gap_y: float = 20.0,
    ):
        if not children:
            return

        parent_x, parent_y = imnodes.get_node_grid_space_pos(anchor.id)
        parent_width, parent_height = imnodes.get_node_dimensions(anchor.id)

        child_sizes: list[tuple[Node, float, float]] = []
        for child in children:
            child_width, child_height = imnodes.get_node_dimensions(child.id)
            child_sizes.append((child, child_width, child_height))

        total_height = sum(height for _, _, height in child_sizes)
        total_height += gap_y * (len(child_sizes) - 1)

        start_y = parent_y + (parent_height - total_height) / 2.0
        x = parent_x + parent_width + gap_x

        current_y = start_y
        for child, child_width, child_height in child_sizes:
            logger.debug(f"Placing child node {child.id} at ({x}, {current_y})")
            imnodes.set_node_grid_space_pos(child.id, (x, current_y))
            current_y += child_height + gap_y
    """

    def layout_dag(
        self,
        nodes: list[Node],
        wires: list[Wire],
        start_x: float = 100.0,
        start_y: float = 100.0,
        layer_gap_x: float = 120.0,
        node_gap_y: float = 30.0,
    ):
        if not nodes:
            return

        # Build adjacency and indegree
        children_map: dict[Node, list[Node]] = defaultdict(list)
        indegree: dict[Node, int] = {node: 0 for node in nodes}

        for wire in wires:
            src = wire.output.node
            dst = wire.input.node
            children_map[src].append(dst)
            indegree[dst] += 1

        # Roots = nodes with no incoming edges
        roots = [node for node in nodes if indegree[node] == 0]
        if not roots:
            # fallback if graph has cycles or weird structure
            roots = [nodes[0]]

        # Assign layers using longest-path style BFS
        layer_of: dict[Node, int] = {node: 0 for node in nodes}
        queue = deque(roots)

        while queue:
            node = queue.popleft()
            current_layer = layer_of[node]

            for child in children_map[node]:
                next_layer = current_layer + 1
                if next_layer > layer_of[child]:
                    layer_of[child] = next_layer
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)

        # Group nodes by layer
        layers: dict[int, list[Node]] = defaultdict(list)
        for node, layer in layer_of.items():
            layers[layer].append(node)

        # Sort nodes within each layer for stable results
        for layer_nodes in layers.values():
            layer_nodes.sort(key=lambda n: n.id)

        # Compute x position per layer
        sorted_layer_ids = sorted(layers.keys())
        layer_x: dict[int, float] = {}
        current_x = start_x

        for layer in sorted_layer_ids:
            layer_nodes = layers[layer]
            max_width = max(node.width for node in layer_nodes)
            layer_x[layer] = current_x
            current_x += max_width + layer_gap_x

        # Place nodes stacked vertically in each layer
        for layer in sorted_layer_ids:
            layer_nodes = layers[layer]

            total_height = (
                sum(node.height for node in layer_nodes)
                + node_gap_y * (len(layer_nodes) - 1)
            )

            current_y = start_y
            x = layer_x[layer]

            for node in layer_nodes:
                node.position = (x, current_y)
                current_y += node.height + node_gap_y
