from fastapi import FastAPI


def app(_=None) -> FastAPI:
    """
    Initialise FastAPI app.
    """
    from core.configuration.server import Server

    return Server().get_app()
