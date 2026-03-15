from crunge.engine.imgui.widget import Dock

from .page import Page
from .graph import Graph
from .graph_layout import GraphLayout

from .session import Session


class GraphPage(Page):
    def __init__(self, name: str, title: str):
        super().__init__(name, title)
        self.dragged = None
        self.graph_layout = GraphLayout()
        self.graph = Graph()
        self.graph.graph_layout = self.graph_layout
        self.graph.make_current()

    def _create(self):
        super()._create()
        self.graph_dock = Dock("Graph", [self.graph])
        # RuntimeError: Child already has a owner, it must be removed first.
        #self.graph_dock.add_child(self.graph)
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
        #self.graph.update(delta_time)

