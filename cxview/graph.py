from typing import TYPE_CHECKING, Optional
from contextvars import ContextVar

from loguru import logger

from crunge import imgui, imnodes

from .pin import Pin
from .wire import Wire

if TYPE_CHECKING:
    from .node import Node

current_graph: ContextVar[Optional["Graph"]] = ContextVar("current_graph", default=None)


class Graph:
    def __init__(self):
        self.nodes: list[Node] = []
        self.node_map: dict[int, Node] = {}
        self.wires: list[Wire] = []
        self.wire_map: dict[int, Wire] = {}
        self.pins: list[Pin] = []
        self.pin_map: dict[int, Pin] = {}

    def make_current(self):
        current_graph.set(self)

    @classmethod
    def get_current(cls) -> Optional["Graph"]:
        return current_graph.get()

    def reset(self):
        for node in self.nodes:
            node.reset()

    def add_node(self, node: "Node"):
        self.nodes.append(node)
        self.node_map[node.id] = node
        return node

    def remove_node(self, node: "Node"):
        self.nodes.remove(node)
        self.node_map.pop(node.id)

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
        self.remove_wire(wire)

    def update(self, delta_time: float):
        for node in self.nodes:
            node.update(delta_time)

    def draw(self):
        imgui.begin("Node Editor")

        imnodes.begin_node_editor()

        for node in self.nodes:
            node.draw()
        for wire in self.wires:
            wire.draw()

        def cb(node, data):
            # print(node, data)
            pass

        cb_data = True
        # imnodes.mini_map(0.1, imnodes.MiniMapLocation.TOP_LEFT, cb, cb_data)
        imnodes.mini_map(0.1, imnodes.MiniMapLocation.TOP_RIGHT, cb, cb_data)
        # imnodes.mini_map()
        imnodes.end_node_editor()

        if (result := imnodes.is_link_created(0, 0))[0]:
            logger.debug(result)
            output = self.pin_map[result[1]]
            input = self.pin_map[result[2]]
            logger.debug(f"output:  {output}")
            logger.debug(f"input:  {input}")
            self.connect(output, input)

        if (result := imnodes.is_link_destroyed(0))[0]:
            wire = self.wire_map[result[1]]
            logger.debug(f"destroyed: {wire}")
            self.disconnect(wire)

        imgui.end()
