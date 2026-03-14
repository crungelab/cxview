from contextlib import contextmanager

from crunge import imgui, imnodes


class Pin:
    id_counter = 0

    def __init__(self, node, name):
        self.id = Pin.id_counter
        Pin.id_counter += 1
        self.node = node
        self.name = name
        self.wires = []
        self.x = 0
        self.y = 0
        self.node.add_pin(self)

    def destroy(self):
        pass

    def add_wire(self, wire):
        self.wires.append(wire)

    def remove_wire(self, wire):
        self.wires.remove(wire)

    def set_position(self, pos):
        self.x, self.y = pos

    def get_position(self):
        return (self.x, self.y)

    def draw(self):
        self.begin()
        self.end()

    def __enter__(self):
        self.begin()

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.end()

    @contextmanager
    def drawing(self):
        self.begin()
        try:
            yield
        finally:
            self.end()

    def begin(self):
        pass

    def end(self):
        pass


class Input(Pin):
    def __init__(self, node, name):
        super().__init__(node, name)

    def begin(self):
        imnodes.begin_input_attribute(self.id)
        # imgui.text(self.name)

    def end(self):
        imnodes.end_input_attribute()

"""
class Output(Pin):
    def __init__(self, node, name, action):
        super().__init__(node, name)
        self.action = action

    def begin(self):
        imnodes.begin_output_attribute(self.id)
        # imgui.text(self.name)
        if imgui.button(f"{self.name}##{self.id}"):
            self.action()

    def end(self):
        imnodes.end_output_attribute()
"""

class Output(Pin):
    def __init__(self, node, name):
        super().__init__(node, name)

    def begin(self):
        imnodes.begin_output_attribute(self.id)

    def end(self):
        imnodes.end_output_attribute()

class TogglePin(Output):
    def __init__(self, node, name, action):
        super().__init__(node, name)
        self.action = action
        self.value = False

    def begin(self):
        super().begin()
        # imgui.text(self.name)
        if imgui.radio_button(f"{self.name}##{self.id}", self.value):
            self.value = not self.value
            self.action(self.value)

    def end(self):
        super().end()
