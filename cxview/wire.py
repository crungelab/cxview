from crunge import imnodes

from .pin import Output, Input

class Wire:
    id_counter = 0
    def __init__(self, output: Output, input: Input):
        self.id = Wire.id_counter
        Wire.id_counter += 1
        self.input = input
        self.output = output
        input.add_wire(self)
        output.add_wire(self)

    def destroy(self):
        self.input.remove_wire(self)
        self.output.remove_wire(self)

    def draw(self):
        imnodes.link(self.id, self.input.id, self.output.id)
