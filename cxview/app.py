import sys
from pathlib import Path

from loguru import logger
from clang import cindex

from crunge import imnodes

from crunge.engine import App

from .session import Session
from .menubar import MenubarLocation
from .page import Page

def cxview(path: Path, flags=None):
    app = CxView().create()
    app.load(path, flags)
    app.use_all()
    app.show_channel("main")
    app.run()


class CxView(App):
    def __init__(self):
        super().__init__(
            title="CxView",
            resizable=True,
        )
        self.package_name = "cxview"

        self.cursor = None
        self.path = None
        self.flags = None
        self.session: Session = None

        self.show_metrics = False
        self.show_style_editor = False
        self.menubar_location = MenubarLocation.WINDOW

        imnodes.create_context()
        imnodes.push_attribute_flag(
            imnodes.AttributeFlags.ENABLE_LINK_DETACH_WITH_DRAG_CLICK
        )

    @property
    def page(self) -> Page:
        return self.view

    @page.setter
    def page(self, value: Page) -> None:
        self.view = value

    def use(self, name):
        logger.debug(f"using: {name}")
        import importlib.util

        spec = importlib.util.find_spec(f"{self.package_name}.pages.{name}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module, install = module, module.install
        install(self)

    def use_all(self, exclude: list[str] = []):
        import importlib.util

        pages_package = f"{self.package_name}.pages"
        spec = importlib.util.find_spec(pages_package)
        if spec is None:
            raise ImportError(f"Cannot find package: {pages_package}")

        # Resolve the actual filesystem path of the pages package
        parent = Path(spec.submodule_search_locations[0])

        exclude = exclude + ["__pycache__", "__init__"]
        excluded = set(exclude)

        names = sorted([p.stem for p in parent.iterdir() if p.stem not in excluded])
        for name in names:
            self.use(name)

    def load(self, path: Path, flags=None):
        self.path = path
        self.flags = flags if flags is not None else []

        if sys.platform == "darwin":
            cindex.Config.set_library_path("/usr/local/opt/llvm@6/lib")
        elif sys.platform == "linux":
            # TODO: make this configurable
            # cindex.Config.set_library_file('/usr/lib/llvm-17/lib/libclang.so.1')
            cindex.Config.set_library_file("/usr/lib/llvm-21/lib/libclang-21.so.1")
        else:
            cindex.Config.set_library_path("C:/Program Files/LLVM/bin")

        tu = cindex.TranslationUnit.from_source(
            self.path,
            args=self.flags,
            # options=cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD,
            options=cindex.TranslationUnit.PARSE_SKIP_FUNCTION_BODIES,
        )

        for diag in tu.diagnostics:
            logger.warning(f"Diagnostic: {diag}")

        self.cursor = tu.cursor
        self.session = Session(self.cursor, self.path)
        self.session.make_current()
