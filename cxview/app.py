import sys
from pathlib import Path

from loguru import logger
from clang import cindex

from crunge import imnodes

from crunge import demo

from .session import Session


resource_root = Path(__file__).parent.parent / "resources"

def cxview(path: Path, flags=None):
    app = CxView().create()
    app.load(path, flags)
    app.use_all()
    app.show_channel("main")
    app.run()

class CxView(demo.Demo):
    def __init__(self):
        super().__init__("CxView", __package__, resource_root)
        self.cursor = None
        self.path = None
        self.flags = None
        self.session: Session = None

        imnodes.create_context()
        imnodes.push_attribute_flag(
            imnodes.AttributeFlags.ENABLE_LINK_DETACH_WITH_DRAG_CLICK
        )

    def load(self, path: Path, flags=None):
        self.path = path
        self.flags = flags if flags is not None else []

        if sys.platform == 'darwin':
            cindex.Config.set_library_path('/usr/local/opt/llvm@6/lib')
        elif sys.platform == 'linux':
            #TODO: make this configurable
            #cindex.Config.set_library_file('/usr/lib/llvm-17/lib/libclang.so.1')
            cindex.Config.set_library_file('/usr/lib/llvm-21/lib/libclang-21.so.1')
        else:
            cindex.Config.set_library_path('C:/Program Files/LLVM/bin')

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
