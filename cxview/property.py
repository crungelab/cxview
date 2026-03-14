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
    def __init__(self, name: str, binding: Binding):
        super().__init__()
        self.name = name
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
        imgui.text(f"{self.name}: {self.value()}")

    def queue_action(self, action: Callable[[], None]):
        self.session.queue_action(action)


class ExpandableProperty(PropertyWidget):
    def __init__(self, name: str, binding: Binding):
        super().__init__(name, binding)
        self.output_pin = TogglePin(name, self.toggle)
        self.output_pin.property = self
        #self.graph.add_pin(self.output_pin)

    def on_added(self):
        logger.debug(f"Adding output pin {self.output_pin} to node {self.node}")
        self.node.add_pin(self.output_pin)
    
    def draw(self):
        self.output_pin.begin()
        self.output_pin.end()

    def toggle(self, value: bool):
        if value:
            self.expand()
        else:
            self.collapse()

    def expand(self):
        pass

    def collapse(self):
        wires:list[Wire] = list(self.output_pin.wires)
        for wire in wires:
            logger.debug(f"wire {wire}")
            logger.debug(f"Hiding child node {wire.input.node.id} of parent {self.id}")
            child_node = wire.input.node
            self.graph.remove_node(child_node)
            self.graph.remove_wire(wire)


class TypeProperty(ExpandableProperty):
    def __init__(self, binding: Binding):
        super().__init__("type", binding)

    def expand(self):
        typ = self.value
        if typ is None:
            return

        node = self.session.create_type_node(typ)
        if node is not None:
            self.graph_layout.place_node_right_of(self.node, node)
            self.graph.add_node(node)
            self.graph.add_wire(Wire(self.output_pin, node.get_pin("parent")))

class ChildrenProperty(ExpandableProperty):
    def __init__(self, binding: Binding):
        super().__init__("children", binding)

    def expand(self):
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
