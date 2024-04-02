from .exception_handlers import ExceptionHandlers
from app.internal.exception_handlers import main_exception

__exception_handlers__ = ExceptionHandlers(
    exception_handlers=(
        # insert your handlers here
        main_exception.exception_handler,
    )
)
