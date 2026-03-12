from cxview.node import RootNode

from crunge.engine import App
from crunge.demo import PageChannel

from ...page import Page
from ...session import Session

class MainPage(Page):
    def __init__(self, name, title):
        super().__init__(name, title)
        session = Session.get_current()
        root_node = RootNode(session.cursor)
        self.graph.add_node(root_node)

def install(app: App):
    app.add_channel(PageChannel(MainPage, "main", "Main"))
