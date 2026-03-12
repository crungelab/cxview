from crunge import demo
from .graph import Graph

from .session import Session


class Page(demo.Page):
    def __init__(self, name: str, title: str):
        super().__init__(name, title)
        self.dragged = None
        #self.graph = Graph()

    @property
    def session(self):
        return Session.get_current()

    @property
    def graph(self):
        return self.session.graph

    def reset(self):
        self.graph.reset()
    
    def start_dnd(self, dragged):
        self.dragged = dragged

    def end_dnd(self):
        dragged = self.dragged
        self.dragged = None
        return dragged

    def update(self, delta_time):
        #self.graph.update(delta_time)
        self.session.update(delta_time)

    def _draw(self):
        self.graph.draw()
        
        super()._draw()
