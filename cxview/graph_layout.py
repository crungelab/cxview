from loguru import logger

from crunge import imnodes

from .node import Node


class GraphLayout:
    def place_node_right_of(self, anchor: Node, node: Node, gap_x: float = 40.0, gap_y: float = 0.0):
        x, y = imnodes.get_node_grid_space_pos(anchor.id)
        width, height = imnodes.get_node_dimensions(anchor.id)
        imnodes.set_node_grid_space_pos(node.id, (x + width + gap_x, y + gap_y))

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
