from crunge import imgui
from crunge.engine import App
from cxview import Page, PageChannel


class Index(Page):
    def _draw(self):
        imgui.begin("Index")
        imgui.text("Welcome to CxView!")
        imgui.end()
        super()._draw()

def install(app: App):
    app.add_channel(PageChannel(Index, "index", "Index"))
