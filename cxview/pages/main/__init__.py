from cxview.node import RootNode

from crunge.engine import App
from cxview import PageChannel

from ...graph_page import GraphPage
from ...session import Session


class MainPage(GraphPage):
    def __init__(self, name, title):
        super().__init__(name, title)
        session = Session.get_current()
        root_node = RootNode(session.cursor)
        self.graph.add_node(root_node)


def install(app: App):
    app.add_channel(PageChannel(MainPage, "main", "Main"))
