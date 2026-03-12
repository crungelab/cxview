from typing import Callable

from clang import cindex
from loguru import logger

from crunge import imgui
from crunge import imnodes

from .wire import Wire

from .pin import Pin, Input, Output
from .session import Session


class Node:
    id_counter = 0

    def __init__(self, name: str):
        self.id = Node.id_counter
        Node.id_counter += 1
        self.name = name
        self.page = None
        self.pins: list[Pin] = []
        self.inputs: list[Input] = []
        self.outputs: list[Output] = []
        self.pin_map: dict[str, Pin] = {}

    def reset(self):
        pass

    def add_pin(self, pin: Pin):
        self.graph.add_pin(pin)
        self.pins.append(pin)
        self.pin_map[pin.name] = pin
        if isinstance(pin, Input):
            self.inputs.append(pin)
        elif isinstance(pin, Output):
            self.outputs.append(pin)

    def get_pin(self, name: str) -> Pin:
        return self.pin_map[name]

    def update(self, delta_time: float):
        pass

    def draw(self):
        self.begin()
        self.end()

    def begin(self):
        imnodes.begin_node(self.id)
        imnodes.begin_node_title_bar()
        with self.inputs[0].drawing():
            imgui.text(self.title)
        imnodes.end_node_title_bar()

    def end(self):
        # for pin in self.pins:
        for pin in self.outputs:
            pin.draw()
        imnodes.end_node()

    @property
    def title(self):
        return self.name

    @property
    def session(self):
        return Session.get_current()

    @property
    def graph(self):
        return self.session.graph

    def queue_action(self, action: Callable[[], None]):
        self.session.queue_action(action)

    def queue_deferred_action(self, action: Callable[[], None]):
        self.session.queue_deferred_action(action)

    def place_node_right_of(
        self, node: "Node", gap_x: float = 40.0, gap_y: float = 0.0
    ):
        x, y = imnodes.get_node_grid_space_pos(self.id)
        width, height = imnodes.get_node_dimensions(self.id)
        imnodes.set_node_grid_space_pos(node.id, (x + width + gap_x, y + gap_y))

    def place_children_right(
        self,
        children: list["Node"],
        gap_x: float = 40.0,
        gap_y: float = 20.0,
    ):
        if not children:
            return

        parent_x, parent_y = imnodes.get_node_grid_space_pos(self.id)
        parent_width, parent_height = imnodes.get_node_dimensions(self.id)

        child_sizes: list[tuple["Node", float, float]] = []
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


class ClangNode(Node):
    def __init__(self, name: str):
        super().__init__(name)
        self.input = Input(self, "parent", self.process)


class CursorNode(ClangNode):
    def __init__(self, name: str, cursor: cindex.Cursor):
        super().__init__(name)
        self.cursor = cursor
        self.children_pin = Output(self, "children", self.process)

    @property
    def title(self):
        return f"{self.name} ({self.cursor.spelling})"

    def queue_process(self):
        self.queue_action(self.process)

    """
    def process(self):
        for cursor in self.cursor.get_children():
            node = self.session.create_cursor_node(cursor)
            if node is not None:
                self.place_node_right_of(node)
                self.graph.add_node(node)
                self.graph.add_wire(Wire(self.get_pin('children'), node.get_pin('parent')))
    """

    def process(self):
        for cursor in self.cursor.get_children():
            node = self.session.create_cursor_node(cursor)
            if node is not None:
                self.place_node_right_of(node)
                self.graph.add_node(node)
                self.graph.add_wire(
                    Wire(self.get_pin("children"), node.get_pin("parent"))
                )

        # self.place_children_right([node for node in self.graph.nodes if node is not self])
        def action():
            children = []
            for wire in self.children_pin.wires:
                logger.debug(f"Found child node {wire.input.node.id} for parent {self.id}")
                children.append(wire.input.node)
            self.place_children_right(children)

        self.queue_action(action)
        #self.queue_deferred_action(action)


    def begin(self):
        super().begin()
        # imgui.text(self.cursor.spelling)


class RootNode(CursorNode):
    def __init__(self, cursor: cindex.Cursor):
        super().__init__("Root", cursor)


class FunctionDeclNode(CursorNode):
    def __init__(self, cursor: cindex.Cursor):
        super().__init__("FunctionDecl", cursor)


class TypedefDeclNode(CursorNode):
    def __init__(self, cursor: cindex.Cursor):
        super().__init__("TypedefDecl", cursor)


class ParmDeclNode(CursorNode):
    def __init__(self, cursor: cindex.Cursor):
        super().__init__("ParmDecl", cursor)
