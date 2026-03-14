from typing import TYPE_CHECKING, Optional, Type, Dict, List, Any, Callable
import contextlib
from contextvars import ContextVar
import re
from pathlib import Path

from clang import cindex
from loguru import logger

from .graph import Graph

current_session: ContextVar[Optional["Session"]] = ContextVar(
    "current_session", default=None
)


class Session:
    def __init__(self, cursor: cindex.Cursor, path: Path) -> None:
        self.cursor = cursor
        self.path = path
        self.graph = Graph()
        self.action_queue = []
        self.deferred_action_queue = []

    def make_current(self):
        current_session.set(self)

    @classmethod
    def get_current(cls) -> Optional["Session"]:
        return current_session.get()

    def queue_action(self, action: Callable[[], None]):
        self.action_queue.append(action)

    def queue_deferred_action(self, action: Callable[[], None]):
        self.deferred_action_queue.append(action)

    def update(self, delta_time):
        while self.action_queue:
            action = self.action_queue.pop(0)
            action()
        self.action_queue = self.deferred_action_queue
        self.deferred_action_queue = []
        self.graph.update(delta_time)

    def is_mappable(self, cursor: cindex.Cursor):
        return self.path == Path(cursor.location.file.name)

    def create_cursor_node(self, cursor: cindex.Cursor):
        if not self.is_mappable(cursor):
            return None
        from .node import RootNode, FunctionDeclNode, TypedefDeclNode, ParmDeclNode, TypeRefNode

        match cursor.kind:
            case cindex.CursorKind.FUNCTION_DECL:
                return FunctionDeclNode(cursor)
            case cindex.CursorKind.TYPEDEF_DECL:
                return TypedefDeclNode(cursor)
            case cindex.CursorKind.PARM_DECL:
                return ParmDeclNode(cursor)
            case cindex.CursorKind.VAR_DECL:
                return RootNode(cursor)
            case cindex.CursorKind.TYPE_REF:
                return TypeRefNode(cursor)
            case _:
                logger.warning(f"Unhandled cursor kind: {cursor.kind}")
                return None

    def create_type_node(self, type: cindex.Type):
        from .node import TypeNode
        return TypeNode(type.spelling, type)

