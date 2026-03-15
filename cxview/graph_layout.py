from collections import defaultdict, deque

from loguru import logger

from crunge import imnodes

from .node import Node
from .wire import Wire


class GraphLayout:
    def __init__(self):
        self.is_dirty = False

    def mark_dirty(self):
        self.is_dirty = True

    def place_node_right_of(
        self, anchor: Node, node: Node, gap_x: float = 40.0, gap_y: float = 0.0
    ):
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

    def layout_dag(
        self,
        nodes: list[Node],
        wires: list[Wire],
        start_x: float = 100.0,
        start_y: float = 100.0,
        #layer_gap_x: float = 120.0,
        layer_gap_x: float = 60.0,
        node_gap_y: float = 30.0,
    ):
        if not nodes:
            return
        
        self.is_dirty = False

        node_set = set(nodes)

        # ------------------------------------------------------------------ #
        # Build adjacency, filtering stale wires.
        # ------------------------------------------------------------------ #
        children_map: dict[Node, list[Node]] = defaultdict(list)
        indegree: dict[Node, int] = {node: 0 for node in nodes}

        for wire in wires:
            src = wire.output.node
            dst = wire.input.node
            if src not in node_set or dst not in node_set:
                continue
            children_map[src].append(dst)
            indegree[dst] += 1

        # Stable child order within every parent
        for node in children_map:
            children_map[node].sort(key=lambda n: n.id)

        roots = [node for node in nodes if indegree[node] == 0]
        if not roots:
            roots = [nodes[0]]
        roots.sort(key=lambda n: n.id)

        # ------------------------------------------------------------------ #
        # Layer assignment: longest-path BFS.
        # ------------------------------------------------------------------ #
        layer_of: dict[Node, int] = {node: 0 for node in nodes}
        remaining_indegree: dict[Node, int] = dict(indegree)
        queue: deque[Node] = deque(roots)

        while queue:
            node = queue.popleft()
            for child in children_map[node]:
                if layer_of[node] + 1 > layer_of[child]:
                    layer_of[child] = layer_of[node] + 1
                remaining_indegree[child] -= 1
                if remaining_indegree[child] == 0:
                    queue.append(child)

        # ------------------------------------------------------------------ #
        # Subtree height: bottom-up accumulation.
        #
        # The "subtree height" of a node is the total vertical space its
        # entire descendant block needs, including gaps between siblings.
        # Leaf nodes occupy exactly their own height.  An internal node
        # occupies max(its own height, sum-of-children-subtree-heights +
        # gaps), because the children must fit beside it without overlap.
        # ------------------------------------------------------------------ #
        subtree_h: dict[Node, float] = {}

        def compute_subtree_h(node: Node) -> float:
            if node in subtree_h:
                return subtree_h[node]
            children = children_map.get(node, [])
            if not children:
                result = node.height
            else:
                children_total = sum(compute_subtree_h(c) for c in children)
                children_total += node_gap_y * (len(children) - 1)
                result = max(node.height, children_total)
            subtree_h[node] = result
            return result

        for root in roots:
            compute_subtree_h(root)
        # Handle any nodes disconnected from all roots
        for node in nodes:
            if node not in subtree_h:
                compute_subtree_h(node)

        # ------------------------------------------------------------------ #
        # X positions per layer.
        # ------------------------------------------------------------------ #
        layers: dict[int, list[Node]] = defaultdict(list)
        for node in nodes:
            layers[layer_of[node]].append(node)

        sorted_layer_ids = sorted(layers.keys())
        layer_x: dict[int, float] = {}
        current_x = start_x
        for layer in sorted_layer_ids:
            max_width = max(node.width for node in layers[layer])
            layer_x[layer] = current_x
            current_x += max_width + layer_gap_x

        # ------------------------------------------------------------------ #
        # Y positions: top-down recursive placement.
        #
        # Each node is given a "slot" whose height equals its subtree_h.
        # The node itself is centered within that slot, and its children's
        # slots are stacked contiguously inside it.  Because slot sizes are
        # computed bottom-up from actual subtree heights, siblings at every
        # layer are guaranteed non-overlapping.
        # ------------------------------------------------------------------ #
        node_y: dict[Node, float] = {}

        def place(node: Node, slot_top: float):
            slot_h = subtree_h[node]
            # Center this node vertically within its slot
            node_y[node] = slot_top + (slot_h - node.height) / 2.0

            children = children_map.get(node, [])
            if not children:
                return

            children_total = sum(subtree_h[c] for c in children)
            children_total += node_gap_y * (len(children) - 1)

            # Stack children's slots, themselves centered in the parent slot
            child_slot_top = slot_top + (slot_h - children_total) / 2.0
            for child in children:
                place(child, child_slot_top)
                child_slot_top += subtree_h[child] + node_gap_y

        # Place each root, stacking their subtree slots from start_y
        current_y = start_y
        for root in roots:
            place(root, current_y)
            current_y += subtree_h[root] + node_gap_y

        # Place any nodes unreachable from roots (isolated / cyclic fallback)
        for node in nodes:
            if node not in node_y:
                node_y[node] = current_y
                current_y += node.height + node_gap_y

        # ------------------------------------------------------------------ #
        # Apply positions.
        # ------------------------------------------------------------------ #
        for node in nodes:
            x = layer_x[layer_of[node]]
            y = node_y[node]
            #logger.debug(f"Placing node {node.id} at ({x:.1f}, {y:.1f})")
            node.position = (x, y)