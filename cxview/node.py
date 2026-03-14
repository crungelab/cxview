from typing import Callable

from clang import cindex
from loguru import logger

from crunge import imgui
from crunge import imnodes
from crunge.engine.imgui.widget import Widget

from .wire import Wire

from .pin import Pin, Input, Output, TogglePin
from .session import Session
from .graph import Graph

class Node(Widget):
    id_counter = 0

    def __init__(self, name: str):
        super().__init__()
        self.id = Node.id_counter
        Node.id_counter += 1
        self.name = name
        self.page = None
        self.pins: list[Pin] = []
        self.inputs: list[Input] = []
        self.outputs: list[Output] = []
        self.pin_map: dict[str, Pin] = {}

    @property
    def title(self):
        return self.name

    @property
    def session(self):
        return Session.get_current()

    @property
    def graph(self):
        return Graph.get_current()

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


    def _begin(self):
        imnodes.begin_node(self.id)
        imnodes.begin_node_title_bar()
        # with self.inputs[0].drawing():
        with self.inputs[0]:
            imgui.text(self.title)
        imnodes.end_node_title_bar()

    def _end(self):
        # for pin in self.pins:
        for pin in self.outputs:
            pin.draw()
        imnodes.end_node()

    def queue_action(self, action: Callable[[], None]):
        self.session.queue_action(action)

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
        self.parent_pin = Input(self, "parent")


class TypeNode(ClangNode):
    def __init__(self, name: str, type: cindex.Type):
        super().__init__(name)
        self.type = type

    def _begin(self):
        super()._begin()
        imgui.text(self.type.spelling)


class CursorNode(ClangNode):
    def __init__(self, name: str, cursor: cindex.Cursor):
        super().__init__(name)
        self.cursor = cursor
        # self.children_pin = Output(self, "children", self.process)
        self.type_pin = TogglePin(self, "type", self.toggle_type)
        self.children_pin = TogglePin(self, "children", self.toggle_children)

    @property
    def title(self):
        return f"{self.name} ({self.cursor.spelling})"

    """
    def toggle_children(self, value: bool):
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
    """

    def toggle_type(self, value: bool):
        if value:
            self.show_type()
        else:
            self.hide_type()

    def show_type(self):
        typ = self.cursor.type
        if typ is None:
            return

        node = self.session.create_type_node(typ)
        if node is not None:
            self.place_node_right_of(node)
            self.graph.add_node(node)
            self.graph.add_wire(Wire(self.get_pin("type"), node.get_pin("parent")))

    def hide_type(self):
        pass

    def toggle_children(self, value: bool):
        if value:
            self.show_children()
        else:
            self.hide_children()

    def show_children(self):
        for cursor in self.cursor.get_children():
            node = self.session.create_cursor_node(cursor)
            if node is not None:
                self.place_node_right_of(node)
                self.graph.add_node(node)
                self.graph.add_wire(
                    Wire(self.get_pin("children"), node.get_pin("parent"))
                )

        def action():
            children = []
            for wire in self.children_pin.wires:
                logger.debug(
                    f"Found child node {wire.input.node.id} for parent {self.id}"
                )
                children.append(wire.input.node)
            self.place_children_right(children)

        self.queue_action(action)

    def hide_children(self):
        logger.debug(f"Hiding children before: {self.graph.nodes}")
        # Have to make a copy of the wires list because we'll be modifying it during iteration
        wires = list(self.children_pin.wires)
        for wire in wires:
            logger.debug(f"wire {wire}")
            logger.debug(f"Hiding child node {wire.input.node.id} of parent {self.id}")
            child_node = wire.input.node
            self.graph.remove_node(child_node)
            self.graph.remove_wire(wire)

        logger.debug(f"Hiding children after: {self.graph.nodes}")

    """
    def hide_children(self):
        logger.debug(f"Hiding children before: {self.graph.nodes}")
        for wire in self.children_pin.wires:
            logger.debug(f"wire {wire}")
            logger.debug(f"Hiding child node {wire.input.node.id} of parent {self.id}")
            child_node = wire.input.node
            self.graph.remove_node(child_node)
            self.graph.remove_wire(wire)

        logger.debug(f"Hiding children after: {self.graph.nodes}")
    """


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


class TypeRefNode(CursorNode):
    def __init__(self, cursor: cindex.Cursor):
        super().__init__("TypeRef", cursor)
