from typing import TYPE_CHECKING, Callable
from contextlib import contextmanager

from crunge import imgui, imnodes

if TYPE_CHECKING:
    from .node import Node
    from .wire import Wire

class Pin:
    id_counter = 0

    def __init__(self, name: str):
        self.id = Pin.id_counter
        Pin.id_counter += 1
        self.name = name
        self.node: "Node" = None
        self.wires: list["Wire"] = []

    def destroy(self):
        pass

    def add_wire(self, wire: "Wire"):
        self.wires.append(wire)

    def remove_wire(self, wire: "Wire"):
        self.wires.remove(wire)

    def draw(self):
        self.begin()
        self.end()

    def __enter__(self):
        self.begin()

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.end()

    def begin(self):
        pass

    def end(self):
        pass


class Input(Pin):
    def __init__(self, name: str):
        super().__init__(name)

    def begin(self):
        imnodes.begin_input_attribute(self.id)

    def end(self):
        imnodes.end_input_attribute()


class Output(Pin):
    def __init__(self, name: str):
        super().__init__(name)

    def expand(self):
        pass

    def collapse(self):
        pass

    def begin(self):
        imnodes.begin_output_attribute(self.id)

    def end(self):
        imnodes.end_output_attribute()


class ExpandablePin(Output):
    def __init__(self, name: str, action: Callable[[bool], None]):
        super().__init__(name)
        self.action = action
        self._expanded = False

    @property
    def expanded(self):
        return self._expanded

    @expanded.setter
    def expanded(self, value: bool):
        self._expanded = value
        self.action(self._expanded)

    def toggle(self):
        self.expanded = not self.expanded

    def expand(self):
        self.expanded = True

    def collapse(self):
        self.expanded = False

    """
    def begin(self):
        super().begin()
        if imgui.radio_button(f"{self.name}##{self.id}", self.expanded):
            self.toggle()
    """