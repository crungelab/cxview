from crunge.engine.imgui.widget import Dock

from .page import Page
from .graph import Graph

from .session import Session


class GraphPage(Page):
    def __init__(self, name: str, title: str):
        super().__init__(name, title)
        self.dragged = None
        self.graph = Graph()
        self.graph.make_current()

    def _create(self):
        super()._create()
        self.graph_dock = Dock("Graph", [self.graph])
        self.gui.add_child(self.graph_dock)

    @property
    def session(self):
        return Session.get_current()

    def reset(self):
        self.graph.reset()

    def start_dnd(self, dragged):
        self.dragged = dragged

    def end_dnd(self):
        dragged = self.dragged
        self.dragged = None
        return dragged

    def update(self, delta_time):
        self.session.update(delta_time)
