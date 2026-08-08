class AppError(Exception):
    """Base for every error this app raises on purpose."""

    status_code = 500
    detail = "Internal error"

    def __init__(self, detail: str | None = None) -> None:
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)


class QueueNotOpen(AppError):
    status_code = 404
    detail = "Queue not found or not open"


class NoOneWaiting(AppError):
    status_code = 404
    detail = "No one waiting"


class EntryNotCallable(AppError):
    status_code = 409
    detail = "Entry is not in a state that can be marked done"


class AlreadyInQueue(AppError):
    status_code = 409
    detail = "This email is already in this queue"
