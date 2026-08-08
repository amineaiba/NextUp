from enum import StrEnum

from sqlalchemy import Enum as SAEnum


class QueueStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"


class EntryStatus(StrEnum):
    WAITING = "waiting"
    CALLED = "called"
    SERVING = "serving"
    DONE = "done"
    NO_SHOW = "no_show"
    SKIPPED = "skipped"


class QueueEventType(StrEnum):
    JOINED = "joined"
    CALLED = "called"
    SKIPPED = "skipped"
    NO_SHOW = "no_show"
    DONE = "done"

def db_enum(enum_cls: type[StrEnum], name: str) -> SAEnum:
    # VARCHAR + CHECK, not a native PG type: adding a value later is a normal
    # migration. values_callable stores "waiting", not "WAITING".
    return SAEnum(
        enum_cls,
        name=name,
        native_enum=False,
        create_constraint=True,
        validate_strings=True,
        values_callable=lambda e: [member.value for member in e],
    )
