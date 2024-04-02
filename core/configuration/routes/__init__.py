from app.external.routers import getstatus
from .routes import Routes
from app.internal.routes import admin
from app.internal.routes import default

__routes__ = Routes(
    routers=(
        # insert your routes here
        default.router,
        admin.router,
        getstatus.router

    )
)
