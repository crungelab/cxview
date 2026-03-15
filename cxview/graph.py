from typing import TYPE_CHECKING, Optional
from contextvars import ContextVar

from loguru import logger

from crunge import imgui, imnodes
from crunge.engine.imgui.widget import Widget

from .pin import Pin
from .wire import Wire
from .session import Session

if TYPE_CHECKING:
    from .node import Node
    from .graph_layout import GraphLayout

current_graph: ContextVar[Optional["Graph"]] = ContextVar("current_graph", default=None)


class Graph(Widget):
    def __init__(self):
        super().__init__()

        self.wires: list[Wire] = []
        self.wire_map: dict[int, Wire] = {}
        self.pins: list[Pin] = []
        self.pin_map: dict[int, Pin] = {}

        self.graph_layout: "GraphLayout" = None

    def make_current(self):
        current_graph.set(self)

    @classmethod
    def get_current(cls) -> Optional["Graph"]:
        return current_graph.get()

    @property
    def session(self):
        return Session.get_current()

    @property
    def nodes(self) -> list["Node"]:
        return self.children

    def add_node(self, node: "Node"):
        self.add_child(node)
        return node

    def remove_node(self, node: "Node"):
        self.remove_child(node)

    def add_wire(self, wire: Wire):
        self.wires.append(wire)
        self.wire_map[wire.id] = wire

    def remove_wire(self, wire: Wire):
        wire.destroy()
        self.wires.remove(wire)
        self.wire_map.pop(wire.id)

    def add_pin(self, pin: Pin):
        self.pins.append(pin)
        self.pin_map[pin.id] = pin

    def remove_pin(self, pin: Pin):
        pin.destroy()
        self.pins.remove(pin)
        self.pin_map.pop(pin.id)

    def connect(self, output: Pin, input: Pin):
        self.add_wire(Wire(output, input))

    def disconnect(self, wire: Wire):
        input_node = wire.input.node
        self.remove_node(input_node)
        self.remove_wire(wire)

    def _begin(self):
        imnodes.begin_node_editor()

    def _draw(self):
        super()._draw()

        for wire in self.wires:
            wire.draw()

        def cb(node, data):
            # print(node, data)
            pass

        cb_data = True
        imnodes.mini_map(0.1, imnodes.MiniMapLocation.TOP_RIGHT, cb, cb_data)

    def _end(self):
        imnodes.end_node_editor()

        if (result := imnodes.is_link_dropped(0, False))[0]:
            logger.debug(f"result: {result}")
            output = self.pin_map[result[1]]
            logger.debug(f"dropped: {output}")
            output.toggle()
            """
            def action():
                output.toggle()
            self.session.queue_action(action)
            """

        """
        if (result := imnodes.is_link_created(0, 0))[0]:
            logger.debug(f"result: {result}")
            output = self.pin_map[result[1]]
            input = self.pin_map[result[2]]
            logger.debug(f"output:  {output}")
            logger.debug(f"input:  {input}")
            self.connect(output, input)
        """

        if (result := imnodes.is_link_destroyed(0))[0]:
            logger.debug(f"result: {result}")
            wire = self.wire_map[result[1]]
            logger.debug(f"destroyed: {wire}")
            self.disconnect(wire)
