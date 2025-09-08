"""Stub file for psycopg2.extensions module."""

from typing import Any, Optional, Union, Dict, List, Tuple
from typing_extensions import Protocol

class connection(Protocol):
    def close(self) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
    def cursor(self, cursor_factory: Any = ...) -> Any: ...
    autocommit: bool

class cursor(Protocol):
    def execute(self, query: str, vars: Any = ...) -> None: ...
    def fetchone(self) -> Optional[Any]: ...
    def fetchall(self) -> List[Any]: ...
    def fetchmany(self, size: int = ...) -> List[Any]: ...
    def close(self) -> None: ...

# Connection status constants
STATUS_READY = 0
STATUS_BEGIN = 1
STATUS_IN_TRANSACTION = 2
STATUS_PREPARED = 3
STATUS_IN_ERROR = 4
STATUS_NO_TRANSACTION = 5
STATUS_ACTIVE = 6
STATUS_INTRANS = 7
STATUS_INERROR = 8
STATUS_CONN_OK = 0
STATUS_CONN_BAD = 1
STATUS_CONN_STARTED = 2
STATUS_CONN_MADE = 3
STATUS_CONN_AWAITING_RESPONSE = 4
STATUS_CONN_AUTH_OK = 5
STATUS_CONN_SETENV = 6
STATUS_CONN_SSL_STARTUP = 7
STATUS_CONN_NEEDED = 8
STATUS_CONN_CHECK_WRITABLE = 9
STATUS_CONN_CONSUME = 10
STATUS_CONN_GSS_STARTUP = 11
STATUS_CONN_CHECK_TARGET = 12
STATUS_CONN_CHECK_STANDBY = 13
