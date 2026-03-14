from typing import Callable

from loguru import logger

from crunge import imgui
from crunge.engine.imgui.widget import Widget

from .pin import Pin, Input, Output, TogglePin
from .wire import Wire
from .session import Session
from .graph import Graph


class Binding:
    def __init__(self, getter: Callable[[], any]):
        self._getter = getter

    def get(self):
        return self._getter()


class PropertyWidget(Widget):
    def __init__(self, label: str, binding: Binding | None = None):
        super().__init__()
        self.label = label
        self.binding = binding
        self.node = None

    @property
    def session(self):
        return Session.get_current()

    @property
    def graph(self):
        return Graph.get_current()

    @property
    def graph_layout(self):
        return self.graph.graph_layout

    @property
    def value(self):
        return self.binding.get() if self.binding else None

    def draw(self):
        imgui.text(f"{self.label}: {self.value()}")

    def queue_action(self, action: Callable[[], None]):
        self.session.queue_action(action)


class TypeProperty(PropertyWidget):
    def __init__(self, binding: Binding):
        super().__init__("Type", binding)
        self.output_pin = TogglePin("type", self.toggle_type)

    def draw(self):
        value = self.value
        text = value.spelling if value is not None else "None"

        self.output_pin.begin()
        #imgui.text(f"Type: {text}")
        self.output_pin.end()

    def toggle_type(self, value: bool):
        if value:
            self.show_type()
        else:
            self.hide_type()

    def show_type(self):
        typ = self.value
        if typ is None:
            return

        node = self.session.create_type_node(typ)
        if node is not None:
            self.graph_layout.place_node_right_of(self.node, node)
            self.graph.add_node(node)
            self.graph.add_wire(Wire(self.output_pin, node.get_pin("parent")))

    def hide_type(self):
        pass

class ChildrenProperty(PropertyWidget):
    def __init__(self, binding: Binding):
        super().__init__("Children", binding)
        self.output_pin = TogglePin("children", self.toggle_children)

    def draw(self):
        #children = self.value or []

        self.output_pin.begin()
        #imgui.text(f"Children: {len(children)}")
        self.output_pin.end()

    def toggle_children(self, value: bool):
        if value:
            self.show_children()
        else:
            self.hide_children()

    def show_children(self):
        for cursor in self.value:
            node = self.session.create_cursor_node(cursor)
            if node is not None:
                self.graph_layout.place_node_right_of(self.node, node)
                self.graph.add_node(node)
                self.graph.add_wire(
                    Wire(self.output_pin, node.get_pin("parent"))
                )

        def action():
            children = []
            for wire in self.output_pin.wires:
                logger.debug(
                    f"Found child node {wire.input.node.id} for parent {self.id}"
                )
                children.append(wire.input.node)
            self.graph_layout.place_children_right(self.node, children)


        self.queue_action(action)

    def hide_children(self):
        logger.debug(f"Hiding children before: {self.graph.nodes}")
        # Have to make a copy of the wires list because we'll be modifying it during iteration
        wires = list(self.output_pin.wires)
        for wire in wires:
            logger.debug(f"wire {wire}")
            logger.debug(f"Hiding child node {wire.input.node.id} of parent {self.id}")
            child_node = wire.input.node
            self.graph.remove_node(child_node)
            self.graph.remove_wire(wire)

        logger.debug(f"Hiding children after: {self.graph.nodes}")
