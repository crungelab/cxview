from typing import Callable

from loguru import logger
from clang import cindex
import glm

from crunge import imgui
from crunge import imnodes
from crunge.engine.imgui.widget import Widget

from .pin import Pin, Input, Output
from .session import Session
from .graph import Graph
from .property import Binding, PropertyWidget, TypeProperty, DeclarationProperty, ChildrenProperty


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

    @property
    def position(self):
        return imnodes.get_node_grid_space_pos(self.id)

    @position.setter
    def position(self, value):
        imnodes.set_node_grid_space_pos(self.id, value)

    @property
    def size(self):
        return imnodes.get_node_dimensions(self.id)

    @property
    def width(self, default=180.0):
        w, _ = self.size
        return w if w > 0 else default

    @property
    def height(self, default=100.0):
        _, h = self.size
        return h if h > 0 else default

    def reset(self):
        pass

    def add_property(self, prop: PropertyWidget):
        prop.node = self
        self.add_child(prop)

    def add_pin(self, pin: Pin):
        pin.node = self
        self.graph.add_pin(pin)
        self.pins.append(pin)
        self.pin_map[pin.name] = pin
        if isinstance(pin, Input):
            self.inputs.append(pin)
        elif isinstance(pin, Output):
            self.outputs.append(pin)

    def get_pin(self, name: str) -> Pin:
        return self.pin_map[name]

    def expand(self):
        for pin in self.outputs:
            pin.expand()

    def collapse(self):
        for pin in self.outputs:
            pin.collapse()

    def update(self, delta_time: float):
        pass

    def _begin(self):
        imnodes.begin_node(self.id)
        imnodes.begin_node_title_bar()
        with self.inputs[0]:
            imgui.text(self.title)
        imnodes.end_node_title_bar()

    def _end(self):
        imnodes.end_node()

    def queue_action(self, action: Callable[[], None]):
        self.session.queue_action(action)


class ClangNode(Node):
    def __init__(self, name: str):
        super().__init__(name)
        self.parent_pin = Input("parent")
        self.add_pin(self.parent_pin)


class TypeNode(ClangNode):
    def __init__(self, name: str, type: cindex.Type):
        super().__init__(name)
        self.type = type
        self.add_property(DeclarationProperty(Binding(lambda: self.type.get_declaration())))

    def _begin(self):
        super()._begin()
        imgui.text(str(self.type.kind))


class CursorNode(ClangNode):
    def __init__(self, name: str, cursor: cindex.Cursor):
        super().__init__(name)
        self.cursor = cursor
        self.add_property(TypeProperty(Binding(lambda: self.cursor.type)))
        self.add_property(
            ChildrenProperty(Binding(lambda: list(self.cursor.get_children())))
        )

    @property
    def title(self):
        # return f"{self.name} ({self.cursor.spelling})"
        return self.cursor.spelling

    def _begin(self):
        super()._begin()
        imgui.text(str(self.cursor.kind))


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
