from typing import TYPE_CHECKING, Callable

from loguru import logger

from crunge import imgui
from crunge.engine.imgui.widget import Widget

from .pin import Pin, Input, Output, ExpandablePin
from .wire import Wire
from .session import Session
from .graph import Graph

if TYPE_CHECKING:
    from .node import Node


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
        self.node: "Node" = None

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
        self.output_pin = ExpandablePin(name, self.toggle)

    def on_added(self):
        logger.debug(
            f"ExpandableProperty.on_added() called for {self.name}, value={self.value}"
        )
        logger.debug(f"Adding output pin {self.output_pin} to node {self.node}")
        self.node.add_pin(self.output_pin)

    def draw(self):
        if self.value:
            with self.output_pin:
                imgui.text(f"{self.name}:")
                imgui.same_line()
                if imgui.radio_button(f"##{self.id}", self.output_pin.expanded):
                    self.output_pin.toggle()
        else:
            imgui.text(f"{self.name}: {self.value}")

    def toggle(self, value: bool):
        if value:
            self.expand()
        else:
            self.collapse()

    def expand(self):
        pass

    def collapse(self):
        wires: list[Wire] = list(self.output_pin.wires)

        def action():
            for wire in wires:
                logger.debug(f"wire {wire}")
                logger.debug(
                    f"Hiding child node {wire.input.node.id} of parent {self.id}"
                )
                child_node = wire.input.node
                child_node.collapse()
                self.graph.remove_node(child_node)
                self.graph.remove_wire(wire)

            #self.graph_layout.layout_dag(list(self.graph.nodes), list(self.graph.wires))

        self.queue_action(action)

    def on_create_node(self, node: "Node"):
        if node is None:
            return

        self.graph_layout.place_node_right_of(self.node, node)
        self.graph.add_node(node)
        self.graph.add_wire(Wire(self.output_pin, node.get_pin("parent")))
        #self.graph_layout.layout_dag(list(self.graph.nodes), list(self.graph.wires))


class TypeProperty(ExpandableProperty):
    def __init__(self, binding: Binding):
        super().__init__("type", binding)

    def expand(self):
        typ = self.value
        if typ is None:
            return

        node = self.session.create_type_node(typ)
        self.on_create_node(node)
        '''
        if node is not None:
            self.graph_layout.place_node_right_of(self.node, node)
            self.graph.add_node(node)
            self.graph.add_wire(Wire(self.output_pin, node.get_pin("parent")))
            self.graph_layout.layout_dag(list(self.graph.nodes), list(self.graph.wires))
        '''

class DeclarationProperty(ExpandableProperty):
    def __init__(self, binding: Binding):
        super().__init__("declaration", binding)

    def expand(self):
        decl = self.value
        if decl is None:
            return

        node = self.session.create_cursor_node(decl)
        self.on_create_node(node)
        '''
        if node is not None:
            self.graph_layout.place_node_right_of(self.node, node)
            self.graph.add_node(node)
            self.graph.add_wire(Wire(self.output_pin, node.get_pin("parent")))
            self.graph_layout.layout_dag(list(self.graph.nodes), list(self.graph.wires))
        '''

class ChildrenProperty(ExpandableProperty):
    def __init__(self, binding: Binding):
        super().__init__("children", binding)

    #TODO: This is calling layout_dag multiple times, which might be inefficient
    def expand(self):
        for cursor in self.value:
            node = self.session.create_cursor_node(cursor)
            self.on_create_node(node)

    '''
    def expand(self):
        for cursor in self.value:
            node = self.session.create_cursor_node(cursor)
            if node is not None:
                self.graph_layout.place_node_right_of(self.node, node)
                self.graph.add_node(node)
                self.graph.add_wire(Wire(self.output_pin, node.get_pin("parent")))
        def action():
            children = []
            for wire in self.output_pin.wires:
                logger.debug(
                    f"Found child node {wire.input.node.id} for parent {self.id}"
                )
                children.append(wire.input.node)
            self.graph_layout.layout_dag(list(self.graph.nodes), list(self.graph.wires))

        self.queue_action(action)
    '''